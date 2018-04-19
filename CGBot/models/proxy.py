from sqlalchemy import Column, String, Integer, Boolean

from . import Base


class Proxy(Base):
    __tablename__ = 'proxy'

    proxy_id = Column(Integer, primary_key=True, nullable=False)
    link = Column(String(230))
    name = Column(String(30))
    is_active = Column(Boolean, default=True)

