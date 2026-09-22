# Contributing

## Branching

Conflict evidence branch policy: preserve both policy decisions and record the conflict and test results in the engineering report.

Create focused feature branches from `main` using a descriptive prefix, for example `feat/mcp-agent` or `fix/auth-status`. Keep commits small and meaningful. Open a pull request into `main`; do not develop directly on `main`.

Before requesting review, run the relevant pytest suites, `git diff --check`, and the Docker build when Docker Desktop is available. Resolve merge conflicts on the feature branch, rerun tests, and record the resolution in the engineering report.

## Versioning

Use semantic version tags in the form `vMAJOR.MINOR.PATCH`. Increment the patch for compatible fixes, the minor version for backward-compatible functionality, and the major version for breaking API or deployment changes. The container tag must use the same release version as the Git tag, for example `v1.0.0` and `afyaplus-fulfilment:v1.0.0`.

Never commit `.env` or credentials. Use `.env.example` for placeholders and inject secrets at runtime.