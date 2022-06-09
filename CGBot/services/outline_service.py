import logging
import os
from typing import Optional

import requests

from CGBot.const import DEFAULT_TRAFFIC


class OutlineService:
    api_url = os.getenv('VPN_URL')
    @staticmethod
    def create_vpn_user(name: str) -> (str, str):
        id, url = None, None

        response = requests.post(f"{OutlineService.api_url}/access-keys/", verify=False)
        if response.status_code == 201:
            key = response.json()
            id = key['id']
            url = key['accessUrl']

            # переименуем
            data = {
                "name": (None, f"tg_{name}"),
            }
            response = requests.put(
                f"{OutlineService.api_url}/access-keys/{id}/name", files=data, verify=False
            )
            if response.status_code != 204:
                logging.info(f"Rename VPN trouble code: {response.status_code}, e: {response.text}")

            data = {"limit": {"bytes": DEFAULT_TRAFFIC}}
            response = requests.put(
                f"{OutlineService.api_url}/access-keys/{id}/data-limit", json=data, verify=False
            )
            if response.status_code != 204:
                logging.info(f"Set limit VPN trouble code: {response.status_code}, e: {response.text}")
        else:
            logging.info(f"Create VPN trouble code: {response.status_code}, e: {response.text}")
        return id, url

    @staticmethod
    def get_statistics() -> Optional[dict[int, int]]:
        response = requests.get(f"{OutlineService.api_url}/metrics/transfer", verify=False)
        if (
                response.status_code >= 400
                or "bytesTransferredByUserId" not in response.json()
        ):
            raise Exception("Unable to get metrics")

        data = response.json()
        if 'bytesTransferredByUserId' not in data:
            return None
        return data['bytesTransferredByUserId']

    @staticmethod
    def get_statistics_by_vpn_id(vpn_id) -> Optional[int]:
        response = requests.get(f"{OutlineService.api_url}/metrics/transfer", verify=False)
        if (
                response.status_code >= 400
                or "bytesTransferredByUserId" not in response.json()
        ):
            raise Exception("Unable to get metrics")

        data = response.json()
        if 'bytesTransferredByUserId' not in data:
            return None
        statistics = data['bytesTransferredByUserId']
        if str(vpn_id) in statistics:
            return statistics[str(vpn_id)]
        return None

