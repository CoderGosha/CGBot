from sqlalchemy.ext.declarative import declarative_base

class Base:
    pass


Base = declarative_base(cls=Base)


from .users import Users
from .vpn import VPN




