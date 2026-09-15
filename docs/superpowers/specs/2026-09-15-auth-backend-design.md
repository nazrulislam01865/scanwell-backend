# ScanWell Authentication Backend Design

## Scope
Build the FastAPI backend required by the existing Flutter signup, email verification, password login, and email-OTP login screens. Frontend code is intentionally out of scope for this phase.

## API contract
All endpoints are under `/api/v1/auth`.

- `POST /register`: accepts `name`, `email`, optional `phone`, `password`, and `preferred_login_method` (`password` or `otp`). Creates an inactive-for-login, email-unverified account and sends a six-digit verification code.
- `POST /verify-email`: accepts `email` and six-digit `code`. Verifies the email and returns an access token, refresh token, and user payload.
- `POST /resend-verification`: accepts `email`, invalidates the prior verification code, and sends a new code.
- `POST /login`: accepts `email` and `password`. Requires an active, verified account and returns tokens plus user data.
- `POST /login/otp/request`: accepts `email`. Returns a generic accepted response to avoid account enumeration and sends an OTP only for an active, verified account.
- `POST /login/otp/verify`: accepts `email` and six-digit `code`, then returns tokens plus user data.
- `POST /refresh`: accepts a refresh token and returns a rotated access/refresh pair.
- `GET /me`: authenticates a bearer access token and returns the current user.

## Security
Passwords use Argon2 via `argon2-cffi`. JWTs use HS256 via PyJWT with issuer, audience, token type, subject, JTI, issued-at and expiry claims. Access tokens default to 15 minutes and refresh tokens to 30 days. Verification codes are generated using `secrets`, stored only as HMAC-SHA256 digests, expire after 10 minutes, and are limited to five failed attempts.

The minimum password length is six characters because the current Flutter form enforces six characters. The API normalizes emails to lowercase before persistence and lookup.

Development may return `development_verification_code` in code-issuing responses when `APP_ENV=development` and `AUTH_EXPOSE_DEVELOPMENT_CODES=true`. Production never returns the code. Email delivery supports a logging development driver and SMTP using the Python standard library.

## Persistence
PostgreSQL tables:

- `auth_users`: UUID primary key, name, unique normalized email, optional phone, password hash, preferred login method, email verification timestamp, active flag, created/updated timestamps.
- `auth_verification_codes`: UUID primary key, user FK, purpose (`email_verification` or `login_otp`), HMAC digest, expiry, consumed timestamp, failed attempt count, created timestamp.

## Architecture
Authentication follows the requested module layout: domain contracts/entities, application commands/use cases, SQLAlchemy infrastructure, and FastAPI presentation. Shared infrastructure for settings, database sessions/transactions, password hashing, and JWT handling lives under `app/core/`.

Use cases depend on repository/service protocols and a transaction abstraction rather than FastAPI or SQLAlchemy request objects. This keeps authentication behavior testable without a running PostgreSQL server.

## Error behavior
API errors use FastAPI `detail` objects with stable `code` and human-readable `message`. Duplicate email is HTTP 409. Invalid credentials/codes are HTTP 401. Unverified email is HTTP 403. Disabled account is HTTP 403. Invalid input remains HTTP 422.

## Verification
Unit tests cover password hashing, JWT creation/validation, registration, duplicate account rejection, email verification, password login, OTP request/verify, and refresh behavior. Alembic metadata/imports and Ruff are verified. Database integration requires PostgreSQL/asyncpg and is additionally covered by the migration supplied with this change.
