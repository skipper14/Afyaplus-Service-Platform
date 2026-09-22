# AfyaPlus Engineering Report

## Scope and outcome

The e-commerce fulfilment transplant now has a typed FastAPI service, JWT authentication, Docker packaging, an MCP clinic directory, and an authenticated LangChain agent. The implementation uses a deterministic model/agent path for reproducible evidence and zero LLM spend; the MCP tools remain real and read from `week_5 /week 6/clinics.json`.

## Version-control evidence

The repository history shows a feature branch merged into `main` and a semantic release tag:

```text
*   88a6c42 (HEAD -> main) chore: merge feat-rag-agent-system into main
|\
| * 0fd7ffa (tag: v1.0.0, feat/triage-router, feat-rag-agent-system) feat: finalize RAG agent system docs and audit trail support
|/
* f9bf55d (origin/feature/triage-router) Initial commit: Week 2 AfyaPlus agent project
```

The release image uses the same version name: `afyaplus-fulfilment:v1.0.0`. Branching and semantic version policy is defined in [CONTRIBUTING.md](CONTRIBUTING.md).

### Resolved conflict log

The repository now contains a real resolved conflict on the disposable evidence branch `evidence/conflict-right`. The original project merge at `88a6c42` was clean; the conflict below was deliberately created in `CONTRIBUTING.md`, resolved by preserving both policy requirements, and verified with the full test suite:

```text
$ git switch evidence/conflict-right
$ git merge evidence/conflict-third
Auto-merging CONTRIBUTING.md
CONFLICT (content): Merge conflict in CONTRIBUTING.md
Automatic merge failed; fix conflicts and then commit the result.
$ git status --short
UU CONTRIBUTING.md
$ git diff -- CONTRIBUTING.md
<<<<<<< HEAD
Conflict evidence branch policy: record the conflict and test results in the engineering report.
=======
Conflict evidence branch policy: preserve both policy decisions during resolution.
>>>>>>> evidence/conflict-third
$ git diff --check
$ git add CONTRIBUTING.md
$ git commit -m "merge: resolve contributing policy conflict"
[evidence/conflict-right a940863] merge: resolve contributing policy conflict
$ git --no-pager log --oneline --graph -4
*   a940863 merge: resolve contributing policy conflict
|\
| * a98e2cc docs: preserve conflict policy decision
* | 9b787e4 docs: clarify report conflict policy
|/
$ /usr/local/bin/python3 -m pytest -q week_5\ /week\ 6/test_agent_service.py week_5\ /week\ 6/test_mcp_server.py week_5\ /week\ 6/test_secure_triage_api.py
12 passed, 1 warning
```

The resolved merge commit is `a940863`; its parents are `018e0f5` and `a98e2cc`. The evidence branch is disposable and should not replace `main`; the project release history remains intact.

## Observability and trace reconstruction

The trace below reconstructs one request across the API, agent, and MCP tool logs. Sensitive credentials are omitted. The request is authenticated by the existing JWT dependency before the agent runs.

```text
API request
POST /agent/ask
Authorization: Bearer <operator JWT>
question: Which clinics have available diagnostics in Kenya?

API/auth
HTTP 200
agent endpoint accepted the existing operator JWT

Agent plan
LangChain StructuredTool -> find_available_clinics(min_slots=1, country="KE")
LangChain StructuredTool -> search_clinics(query="diagnostics", country="KE")

MCP stderr
{"event":"mcp_call","name":"find_available_clinics","outcome":"ok"}
{"event":"mcp_call","name":"search_clinics","outcome":"ok"}

Agent synthesis / API response
HTTP 200
{"answer":"Available diagnostics clinics in KE: AfyaPlus Nairobi Central (12 slots).","tools_called":["find_available_clinics","search_clinics"],"grounded":true}
```

This trace is reproducible through the curl command and transcript in [week_5 /week 6/README.md](week_5%20/week%206/README.md). The MCP server writes one JSON log line per call to stderr so stdio protocol output remains clean. The unsupported-policy test reconstructs the safe failure path: it returns `grounded: false`, calls no tools, and says the clinic data cannot answer the question.

## Verification summary

The focused regression suites completed with `12 passed`: three authenticated-agent tests, four MCP tests, and five FastAPI security tests. The Docker image `afyaplus-fulfilment:v1.0.0` built successfully, imported the agent inside the container, and ran as the non-root `app` user.

## Decision

The platform is suitable for a controlled pilot with the conditions in the stakeholder memo: keep the deterministic path or add a model only behind the same contract, retain JWT and runtime-secret controls, and require trace review for any expansion of the clinic data domain.