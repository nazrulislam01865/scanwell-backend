# ScanWell FastAPI Backend

FastAPI backend for the ScanWell Flutter application. The current backend phase includes account registration, email verification, password login, email OTP login, forgot/reset password, JWT access tokens, persisted rotating refresh sessions, logout, logout-all, and the authenticated current-user endpoint.

## 1. Requirements

- Python 3.12+
- `uv`
- Docker + Docker Compose (recommended for local PostgreSQL)

## 2. First-time setup

```bash
cp .env.example .env
```

Replace `SECRET_KEY` with a long random value before using the API outside local development:

```bash
openssl rand -hex 32
```

Put the generated value in `.env`.

Install/sync Python dependencies:

```bash
uv sync
```

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Run migrations:

```bash
uv run alembic upgrade head
```

Start FastAPI:

```bash
uv run fastapi dev app/main.py
```

Swagger UI is available at `http://127.0.0.1:8000/docs`.

## 3. Authentication API

Base path: `/api/v1/auth`

### Create account

`POST /api/v1/auth/register`

```json
{
  "name": "Nazrul Islam",
  "email": "nazrul@example.com",
  "phone": "+8801712345678",
  "password": "secret123",
  "preferred_login_method": "password"
}
```

`preferred_login_method` accepts `password` or `otp`. The password is still required during registration so the account can use password login later.

In development only, when `AUTH_EXPOSE_DEVELOPMENT_CODES=true`, code-issuing responses include `development_verification_code`. Production never exposes verification codes in API responses.

### Verify signup email

`POST /api/v1/auth/verify-email`

```json
{
  "email": "nazrul@example.com",
  "code": "123456"
}
```

Successful verification returns the authenticated user plus access and refresh tokens.

### Resend signup verification code

`POST /api/v1/auth/resend-verification`

```json
{
  "email": "nazrul@example.com"
}
```

### Password login

`POST /api/v1/auth/login`

```json
{
  "email": "nazrul@example.com",
  "password": "secret123"
}
```

### Request login OTP

`POST /api/v1/auth/login/otp/request`

```json
{
  "email": "nazrul@example.com"
}
```

The response is intentionally generic so unknown email addresses cannot be enumerated.

### Verify login OTP

`POST /api/v1/auth/login/otp/verify`

```json
{
  "email": "nazrul@example.com",
  "code": "123456"
}
```

### Refresh tokens

`POST /api/v1/auth/refresh`

```json
{
  "refresh_token": "<refresh-token>"
}
```

Refresh tokens are persisted as SHA-256 hashes in `auth_sessions`. Each successful refresh rotates the token; the previous refresh token immediately becomes unusable.

### Logout current session

`POST /api/v1/auth/logout`

```json
{
  "refresh_token": "<refresh-token>"
}
```

### Logout all sessions

`POST /api/v1/auth/logout-all`

Header:

```text
Authorization: Bearer <access-token>
```

### Forgot password

`POST /api/v1/auth/password/forgot`

```json
{
  "email": "nazrul@example.com"
}
```

### Reset password

`POST /api/v1/auth/password/reset`

```json
{
  "email": "nazrul@example.com",
  "code": "123456",
  "new_password": "new-secret123"
}
```

A successful password reset revokes all active refresh sessions for the account.

### Current authenticated user

`GET /api/v1/auth/me`

Header:

```text
Authorization: Bearer <access-token>
```

## 4. Stable authentication errors

Application authentication errors use this shape:

```json
{
  "detail": {
    "code": "INVALID_CREDENTIALS",
    "message": "Email or password is incorrect."
  }
}
```

Common codes include `EMAIL_ALREADY_REGISTERED`, `INVALID_CREDENTIALS`, `EMAIL_NOT_VERIFIED`, `ACCOUNT_DISABLED`, `INVALID_VERIFICATION_CODE`, `VERIFICATION_CODE_EXPIRED`, `VERIFICATION_ATTEMPTS_EXCEEDED`, `INVALID_AUTH_TOKEN`, and `AUTH_SESSION_REVOKED`.

## 5. Email delivery

For local development:

```env
EMAIL_DRIVER=log
AUTH_EXPOSE_DEVELOPMENT_CODES=true
```

The OTP is logged and can optionally be returned by the API.

For production on Render Free, use the Brevo HTTPS API rather than SMTP:

```env
APP_ENV=production
EMAIL_DRIVER=brevo
AUTH_EXPOSE_DEVELOPMENT_CODES=false
BREVO_API_KEY=xkeysib-your-api-key
BREVO_TIMEOUT_SECONDS=15
EMAIL_FROM_NAME=ScanWell
EMAIL_FROM_ADDRESS=your-verified-sender@gmail.com
```

`EMAIL_FROM_ADDRESS` must exactly match a sender that has been registered and verified in Brevo. The Brevo provider sends through `POST https://api.brevo.com/v3/smtp/email` over HTTPS and does not require SMTP credentials, a Gmail refresh token, or a custom domain.

The application refuses `EMAIL_DRIVER=log` in production. The existing `smtp`, `gmail_api`, and `resend` drivers remain available for environments where they are appropriate.

## 6. Tests

```bash
uv run pytest
uv run ruff check .
```

## 7. Auth persistence

Authentication persistence is created by:

- `20260915_0001_create_auth_tables.py` -> `auth_users`, `auth_verification_codes`
- `20260919_0002_create_auth_sessions.py` -> `auth_sessions`

Passwords are Argon2 hashes. Six-digit verification codes are never stored in plaintext; only an HMAC-SHA256 digest is persisted. Refresh tokens are also never stored in plaintext; `auth_sessions` stores only a SHA-256 digest of the current rotating refresh token.
