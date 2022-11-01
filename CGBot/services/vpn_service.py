import json
import logging
import os
from typing import List, Optional

from CGBot.services.outline_service import OutlineService


class VPNService:
    vpn_services = []

    @staticmethod
    def load_vpn_from_config(file_path):
        if not os.path.exists(file_path):
            raise FileExistsError(f"{file_path} is not found")

        with open(file_path) as vpn_file:
            parsed_json = json.load(vpn_file)
            for v in parsed_json["OutlineServers"]:
                vpn = OutlineService(vpn_id=v["Id"], api_url=v["Url"], name=v["Name"])
                VPNService.vpn_services.append(vpn)
                logging.info(f"Loading vpn: {vpn.name}")

        logging.info(f"Loading vpns: {len(VPNService.vpn_services)}")

    @staticmethod
    def get_vpns() ->List[OutlineService]:
        return VPNService.vpn_services

    @staticmethod
    def get_vpn_by_name(name) -> Optional[OutlineService]:
        for v in VPNService.vpn_services:
            if v.name == name:
                return v

        return None

    @staticmethod
    def get_vpn_by_id(vpn_id) -> Optional[OutlineService]:
        for v in VPNService.vpn_services:
            if v.vpn_id == vpn_id:
                return v

        return None



