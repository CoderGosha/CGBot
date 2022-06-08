import asyncio
import os

import logging
from CGBot.cg_bot import CGBot

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    vpn_url = os.getenv('VPN_URL')
    use_webhook = bool(int(os.getenv('USE_WEBHOOK', False)))
    webhook_domain = os.getenv('WEBHOOK_DOMAIN', '127.0.0.1')
    webhook_port = int(os.getenv('WEBHOOK_PORT', os.getenv('PORT', 80)))

    if telegram_token is None:
        logging.error("No found telegram_token: %s" % telegram_token)
        exit(0)

    if vpn_url is None:
        logging.error("No found vpn_url: %s" % vpn_url)
        exit(0)

    cgbot = CGBot(token=telegram_token)
    asyncio.run(cgbot.start())


