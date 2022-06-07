from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class Base:
    pass


Base = declarative_base(cls=Base)


from .users import Users
from .vpn import VPN


def make_session_maker(url):
    engine = create_engine(url)
    return sessionmaker(bind=engine)

