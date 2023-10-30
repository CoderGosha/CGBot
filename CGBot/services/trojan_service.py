class TrojanService:
    def __init__(self, vpn_id, api_url, name, vpn_type):
        self.vpn_id = vpn_id
        self.name = name
        self.api_url = api_url
        self.vpn_type = vpn_type

    def create_vpn_user(self, name: str) -> (str, str):
        id, url = self.vpn_id, self.api_url
        return id, url
