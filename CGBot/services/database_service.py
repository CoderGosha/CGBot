import os
from typing import Optional, List

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from CGBot.const import DEFAULT_DATABASE
from CGBot.models import Base, VPN
from CGBot.models.vpn import VPNUserState


class DBService:
    db_url = os.getenv('DATABASE_URL', DEFAULT_DATABASE)
    engine = create_engine(db_url)

    @staticmethod
    def init_db():
        Base.metadata.create_all(DBService.engine)

    @staticmethod
    def check_vpn_state(user_id) -> Optional[VPNUserState]:
        session = Session(DBService.engine, future=True)
        # with Session(DBService.engine) as session:
        statement = select(VPN).filter_by(user_id=user_id)
        result = session.execute(statement).scalars().first()
        if result is None:
            return None

        return result.state

    @staticmethod
    def vpn_request(user_id, name: str, user_info: str):
        with Session(DBService.engine) as session:
            vpn = VPN(user_id=user_id, state=VPNUserState.Request, vpn_name=name, user_info=user_info)
            session.add(vpn)
            session.commit()

    @staticmethod
    def vpn_accept(user_id, id, url):
        with Session(DBService.engine) as session:
            vpn = session.execute(select(VPN).filter_by(user_id=user_id)).scalar_one()
            vpn.state = VPNUserState.Ready
            vpn.vpn_url = url
            vpn.vpn_uid = id
            session.commit()


    @staticmethod
    def vpn_get_link(user_id) -> Optional[str]:
        session = Session(DBService.engine, future=True)
        statement = select(VPN).filter_by(user_id=user_id)
        result = session.execute(statement).scalars().first()
        if result is None:
            return None

        return result.vpn_url

    @staticmethod
    def vpn_by_user_id(user_id) -> Optional[VPN]:
        session = Session(DBService.engine, future=True)
        statement = select(VPN).filter_by(user_id=user_id)
        result = session.execute(statement).scalars().first()
        if result is None:
            return None

        return result

    @staticmethod
    def vpn_active_request() -> Optional[List[VPN]]:
        session = Session(DBService.engine, future=True)
        statement = select(VPN).filter_by(state=VPNUserState.Request)
        result = session.execute(statement).scalars().all()
        if result is None:
            return None

        return result

    @staticmethod
    def vpn_get_all_users() -> Optional[List[VPN]]:
        session = Session(DBService.engine, future=True)
        statement = select(VPN)
        result = session.execute(statement).scalars().all()
        if result is None:
            return None

        return result
