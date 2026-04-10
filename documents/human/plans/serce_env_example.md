# Serce — .env.example

Plik do umieszczenia w `serce/backend/.env.example`.
Wszystkie klucze wymagane chyba że oznaczone jako opcjonalne.

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/serce

# JWT
SECRET_KEY=change-me-to-random-32-char-string
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# SMS OTP (SMSAPI.pl)
SMSAPI_TOKEN=
SMSAPI_SENDER=Serce          # opcjonalne, domyślna nazwa nadawcy

# Email (Resend.com)
RESEND_API_KEY=
EMAIL_FROM=noreply@serce.pl

# CAPTCHA (hCaptcha)
HCAPTCHA_SECRET=
HCAPTCHA_SITEKEY=            # używany przez frontend, tu dla referencji

# CORS (oddzielone przecinkami)
CORS_ORIGINS=http://localhost:3000,http://localhost:8081

# Business rules (defaults — można nadpisać, sync z SystemConfig)
INITIAL_HEART_GRANT=5
HEART_BALANCE_CAP=50
REQUEST_DEFAULT_EXPIRY_DAYS=30
FLAG_ADMIN_ALERT_DAYS=7

# Rate limiting (SlowAPI)
RATE_LIMIT_LOGIN=10/15minutes
RATE_LIMIT_REGISTER=3/day
RATE_LIMIT_SMS=3/day
RATE_LIMIT_MESSAGES=50/hour
RATE_LIMIT_GIFT=10/day

# Environment
ENV=development              # development | production
LOG_LEVEL=INFO
```

## Uwagi dla Developera

- `SECRET_KEY` — minimum 32 losowe znaki. W produkcji generuj przez `openssl rand -hex 32`.
- `DATABASE_URL` — używa `asyncpg` drivera (async SQLAlchemy). W testach podmień na `postgresql+asyncpg://...test_db`.
- `CORS_ORIGINS` — w produkcji tylko domeny produkcyjne (bez localhost).
- Wartości `INITIAL_HEART_GRANT` i `HEART_BALANCE_CAP` są też w tabeli `SystemConfig` (DB).
  Przy starcie aplikacji: jeśli `SystemConfig` pusty — załaduj z `.env` jako defaults.
- `ENV=production` wyłącza `*` w CORS i włącza secure cookies.
