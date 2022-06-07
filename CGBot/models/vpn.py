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
    user_id = Column(Integer)
    name = Column(String(30))
    link = Column(String(500))
    state = Column(sqlalchemy.Enum(VPNUserState))




