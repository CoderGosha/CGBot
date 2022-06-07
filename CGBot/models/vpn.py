from sqlalchemy import Column, String, Integer, Boolean

from . import Base


class VPN(Base):
    __tablename__ = 'vpn'

    vpn_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(30))
    link = Column(String(500))



