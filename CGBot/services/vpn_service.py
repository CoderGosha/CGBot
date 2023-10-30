import json
import logging
import os
from typing import List, Optional

from CGBot.services.outline_service import OutlineService
from CGBot.services.trojan_service import TrojanService


class VPNService:
    vpn_outline_services = []
    vpn_trojan_services = []

    @staticmethod
    def load_vpn_from_config(file_path):
        if not os.path.exists(file_path):
            raise FileExistsError(f"{file_path} is not found")

        with open(file_path) as vpn_file:
            parsed_json = json.load(vpn_file)
            for v in parsed_json["OutlineServers"]:
                vpn = OutlineService(vpn_id=v["Id"], api_url=v["Url"], name=v["Name"], vpn_type="Outline")
                VPNService.vpn_outline_services.append(vpn)
                logging.info(f"Loading vpn: {vpn.name}")

            for v in parsed_json["TrojanServers"]:
                vpn = TrojanService(vpn_id=v["Id"], api_url=v["Url"], name=v["Name"], vpn_type="Trojan")
                VPNService.vpn_trojan_services.append(vpn)
                logging.info(f"Loading vpn: {vpn.name}")

        logging.info(f"Loading vpns: {len(VPNService.vpn_outline_services)}")

    @staticmethod
    def get_vpns() ->List[OutlineService]:
        return VPNService.vpn_outline_services

    @staticmethod
    def get_vpn_by_name(name) -> Optional[OutlineService]:
        for v in VPNService.vpn_outline_services:
            if v.name == name:
                return v

        for v in VPNService.vpn_trojan_services:
            if v.name == name:
                return v

        return None

    @staticmethod
    def get_vpn_by_id(vpn_id) -> Optional[OutlineService]:
        for v in VPNService.vpn_outline_services:
            if v.vpn_id == vpn_id:
                return v

        for v in VPNService.vpn_trojan_services:
            if v.vpn_id == vpn_id:
                return v

        return None

    @staticmethod
    def get_type_vpns() -> Optional[List[str]]:
        return ["Outline", "Trojan"]

    @staticmethod
    def get_trojan_vpns() -> Optional[List[TrojanService]]:
        return VPNService.vpn_trojan_services





