from enum import Enum

import sqlalchemy
from sqlalchemy import Column, String, Integer, Boolean

from . import Base


class VPNUserState(Enum):
    Request = 1,
    Ready = 2,
    Update = 3,
    Blocked = 4


class VPN(Base):
    __tablename__ = 'vpn'
    vpn_id = Column(Integer, primary_key=True, nullable=False)
    vpn_config_id = Column(Integer, default=1)
    user_id = Column(Integer)
    user_info = Column(String(150))
    vpn_name = Column(String(30))
    vpn_url = Column(String(500))
    vpn_uid = Column(String(30))
    state = Column(sqlalchemy.Enum(VPNUserState))




