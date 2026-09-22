# Stakeholder Decision Memo: AfyaPlus Fulfilment Platform

**Decision:** GO for a controlled pilot, subject to the conditions below.

## What was built

AfyaPlus now has a typed FastAPI fulfilment service with JWT authentication, role checks, health probes, rate limiting, and Docker packaging. A Python MCP server exposes two validated clinic-discovery tools and a read-only catalog resource. An authenticated LangChain agent consumes those MCP tools, answers supported multi-step availability questions, and explicitly declines questions outside the catalog.

## Highest-value component

The highest-value component is the grounded agent-to-MCP path. It combines availability and service searches, returns the intersection, and includes the tool trace. This makes the answer useful while keeping the source data inspectable and the failure mode honest.

## Primary risk and mitigation

**Risk:** The current agent is deterministic and the clinic catalog is small, so coverage may be mistaken for production intelligence. A future model could also overstate an answer if it is allowed to operate outside the catalog.

**Mitigation:** Keep the MCP catalog as the source of truth, require `grounded` output and tool traces, preserve the explicit data-limit response, validate all tool inputs, and expand the catalog and evaluation set before enabling model-generated synthesis. Do not expose real secrets in images or logs.

## Recommendation and conditions

Proceed with a controlled pilot for read-only clinic discovery. Before broader rollout:

1. Tag the exact release commit and publish the matching image tag.
2. Run the MCP Inspector or equivalent protocol checks in CI in addition to unit tests.
3. Replace demo credentials with the production identity provider and rotate `JWT_SECRET` through a secret manager.
4. Add request IDs and centralized log retention for operational trace lookup.
5. Obtain clinical and operations sign-off before adding triage, booking, or medical advice capabilities.

Without those conditions, the recommendation is **NO-GO for unrestricted production use**. The current evidence supports a bounded, read-only pilot, not an autonomous clinical workflow.
