import os

import logging

from CGBot import run_manage_worker, models

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    db_url = os.getenv('DATABASE_URL')
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    use_webhook = bool(int(os.getenv('USE_WEBHOOK', False)))
    webhook_domain = os.getenv('WEBHOOK_DOMAIN', '127.0.0.1')
    webhook_port = int(os.getenv('WEBHOOK_PORT', os.getenv('PORT', 80)))

    if telegram_token is None:
        logging.error("No found telegram_token: %s" % telegram_token)
        exit(0)

    db_session_maker = models.make_session_maker(db_url)
    telegram_updater = run_manage_worker(telegram_token, db_session_maker, use_webhook, webhook_domain, webhook_port)

    telegram_updater.idle()

