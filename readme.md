# CoderGosha Bot
`
set "TELEGRAM_TOKEN=token"
set "USE_WEBHOOK=True"
set "WEBHOOK_DOMAIN=127.0.0.1"
set "WEBHOOK_PORT=80"
set "CERT_DIR=80"
set "BOTAN_KEY=12312312123123"
set "DATABASE_URL=sqlite:///cgbot.sqlite"
`

## Alembic
____________
`
set "PYTHONPATH=."
set "DATABASE_URL=sqlite:///cgbot.sqlite"
alembic upgrade head
alembic revision --autogenerate -m "Added account table"
`
