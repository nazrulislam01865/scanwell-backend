# ScanWell Authentication Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add production-oriented signup, email verification, password login, email-OTP login, JWT refresh, and current-user APIs to the ScanWell FastAPI backend.

**Architecture:** Refactor the touched configuration/database code into the required enterprise package layout, then implement auth as a domain/application/infrastructure/presentation module. Use SQLAlchemy async repositories behind protocols so application behavior can be tested with in-memory fakes.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2 async, PostgreSQL/asyncpg, Alembic, argon2-cffi, PyJWT, pytest.

**Spec:** `docs/superpowers/specs/2026-09-15-auth-backend-design.md`

## Global Constraints
- Preserve `/api/v1/health`.
- Follow the ScanWell module structure supplied by the user.
- Frontend modifications are out of scope.
- Minimum password length is 6 to match the current Flutter validation.
- Never store plaintext passwords or OTP codes.
- Development codes may be returned only when both development environment and explicit expose flag are enabled.

---

### Task 1: Core configuration and security primitives

**Files:**
- Create: `app/core/config/__init__.py`, `settings.py`, `environment.py`
- Create: `app/core/database/__init__.py`, `base.py`, `session.py`, `transaction.py`
- Create: `app/core/security/__init__.py`, `passwords.py`, `jwt.py`
- Modify: `app/main.py`, `app/api/router.py`, `alembic/env.py`, `pyproject.toml`
- Test: `tests/unit/core/test_passwords.py`, `tests/unit/core/test_jwt.py`

**Interfaces:**
- Produces `settings`, `get_db`, `Base`, `SQLAlchemyTransaction`, `hash_password`, `verify_password`, `JWTService`, and token claim validation.

- [ ] Write password and JWT tests first; confirm they fail because security modules do not exist.
- [ ] Implement settings packages, database packages, Argon2 hashing, and JWT service.
- [ ] Run the focused tests and Ruff until green.

### Task 2: Authentication domain and application behavior

**Files:**
- Create: `app/modules/auth/domain/entities.py`, `value_objects.py`, `repositories.py`, `exceptions.py`
- Create: `app/modules/auth/application/dto.py`, `commands.py`, `queries.py`
- Create: `app/modules/auth/application/use_cases/register_user.py`, `verify_email.py`, `login_user.py`, `refresh_token.py`, `request_login_otp.py`, `verify_login_otp.py`, `resend_verification.py`, `get_current_user.py`
- Test: `tests/unit/auth/test_register_user.py`, `test_verify_email.py`, `test_login_user.py`, `test_login_otp.py`, `test_refresh_token.py`

**Interfaces:**
- Consumes password/JWT primitives and repository/email/token protocols.
- Produces framework-independent auth use cases and stable domain exceptions.

- [ ] Write use-case tests with in-memory repository/email/transaction fakes; confirm missing modules fail.
- [ ] Implement domain types, commands, DTOs, exceptions, and use cases with the minimum behavior required by tests.
- [ ] Run all auth unit tests and Ruff until green.

### Task 3: SQLAlchemy persistence and Alembic migration

**Files:**
- Create: `app/modules/auth/infrastructure/models.py`, `repository.py`, `token_service.py`, `email_service.py`
- Create: `alembic/versions/20260915_0001_create_auth_tables.py`
- Modify: `alembic/env.py`
- Test: `tests/unit/auth/test_models.py`

**Interfaces:**
- Implements user/code repository protocols, token service, email delivery, and table metadata used by Alembic.

- [ ] Write model metadata tests first; confirm models are missing.
- [ ] Implement SQLAlchemy models/repositories and migration.
- [ ] Verify model tests and Alembic metadata imports.

### Task 4: FastAPI auth presentation and dependency wiring

**Files:**
- Create: `app/modules/auth/presentation/schemas.py`, `dependencies.py`, `router.py`
- Modify: `app/api/v1/router.py`, `app/bootstrap.py`, `app/main.py`
- Test: `tests/api/test_auth_contract.py`

**Interfaces:**
- Exposes `/api/v1/auth/*` endpoints and bearer authentication for `/me`.

- [ ] Write API contract/schema tests first; confirm auth routes are unavailable.
- [ ] Implement route handlers and dependency factories, map domain errors to stable HTTP responses, and include the auth router.
- [ ] Run API contract tests that do not require PostgreSQL plus the existing health test.

### Task 5: Environment template, documentation, and final verification

**Files:**
- Create: `.env.example`
- Modify: `README.md`

**Interfaces:**
- Documents commands for Docker PostgreSQL, migrations, local API startup, and auth endpoint payloads.

- [ ] Add environment and usage documentation with no real secrets.
- [ ] Run pytest, Ruff, compile checks, and inspect the final tree.
- [ ] Package the completed backend ZIP for handoff.
