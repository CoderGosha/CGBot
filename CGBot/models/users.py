from sqlalchemy import Column, String, Integer, Boolean

from . import Base


class Users(Base):
    __tablename__ = 'users'

    user_id = Column(String(20), primary_key=True, nullable=False)
    user_username = Column(String(130))
    send_notify = Column(Boolean, default=True)
