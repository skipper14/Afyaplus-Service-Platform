from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from auth import authenticate, create_access_token, get_current_user, require_admin
from agent_service import AgentAnswer, answer_question
from rate_limit import SlidingWindow

app = FastAPI(title="AfyaPlus E-commerce Fulfilment API", version="1.0.0")
limiter = SlidingWindow()


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]


class FulfilmentRequest(BaseModel):
    order_id: str = Field(min_length=3, max_length=40, pattern=r"^ORD-[A-Z0-9-]+$")
    destination_country: str = Field(min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    item_count: int = Field(ge=1, le=100)
    priority: Literal["standard", "express"] = "standard"


class FulfilmentResponse(BaseModel):
    order_id: str
    recommendation: Literal["standard", "express"]
    warehouse: Literal["Nairobi", "London"]
    explanation: str


class AgentRequest(BaseModel):
    question: str = Field(min_length=10, max_length=500)


class AgentResponse(BaseModel):
    answer: str
    tools_called: list[str]
    grounded: bool


@app.get("/health")
def health() -> dict[str, str]:
    return {"service": app.title, "version": app.version, "status": "ok"}


@app.post("/token", response_model=TokenResponse)
def token(request: LoginRequest) -> TokenResponse:
    user = authenticate(request.username, request.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(user["sub"], user["role"]), token_type="bearer")


@app.post("/fulfilment", response_model=FulfilmentResponse)
def fulfilment(
    request: FulfilmentRequest,
    user: Annotated[dict, Depends(get_current_user)],
) -> FulfilmentResponse:
    if not limiter.allow(user["sub"]):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    recommendation = "express" if request.priority == "express" or request.item_count > 20 else "standard"
    warehouse = "Nairobi" if request.destination_country in {"KE", "UG", "TZ"} else "London"
    return FulfilmentResponse(
        order_id=request.order_id,
        recommendation=recommendation,
        warehouse=warehouse,
        explanation="Deterministic fulfilment stub selected from order priority, volume, and destination.",
    )


@app.get("/admin/audit")
def audit(_: Annotated[dict, Depends(require_admin)]) -> dict[str, str]:
    return {"status": "ok", "message": "Admin audit access granted"}


@app.post("/agent/ask", response_model=AgentResponse)
def ask_agent(
    request: AgentRequest,
    _: Annotated[dict, Depends(get_current_user)],
) -> AgentResponse:
    """Answer a clinic question through the authenticated MCP-backed LangChain agent."""
    result: AgentAnswer = answer_question(request.question)
    return AgentResponse(
        answer=result.answer,
        tools_called=result.tools_called,
        grounded=result.grounded,
    )