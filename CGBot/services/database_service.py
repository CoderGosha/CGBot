import os
from typing import Optional, List

from alembic import op
from sqlalchemy import create_engine, select, Column, Integer
from sqlalchemy.engine import reflection
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
    def check_vpn_state(user_id, vpn_config_id) -> Optional[VPNUserState]:
        session = Session(DBService.engine, future=True)
        # with Session(DBService.engine) as session:
        statement = select(VPN).filter_by(user_id=user_id).filter_by(vpn_config_id=vpn_config_id)
        result = session.execute(statement).scalars().first()
        if result is None:
            return None

        return result.state

    @staticmethod
    def vpn_request(user_id, name: str, user_info: str, vpn_config_id: str):
        with Session(DBService.engine) as session:
            vpn = VPN(user_id=user_id, state=VPNUserState.Request, vpn_name=name, user_info=user_info,
                      vpn_config_id=vpn_config_id)
            session.add(vpn)
            session.commit()

    @staticmethod
    def vpn_accept(vpn_id, id, url):
        with Session(DBService.engine) as session:
            vpn = session.execute(select(VPN).filter_by(vpn_id=vpn_id)).scalar_one()
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
    def vpn_by_user_id(user_id, vpn_config_id) -> Optional[VPN]:
        session = Session(DBService.engine, future=True)
        statement = select(VPN).filter_by(user_id=user_id).filter_by(vpn_config_id=vpn_config_id)
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
    def vpn_get_all_users(vpn_config_id) -> Optional[List[VPN]]:
        session = Session(DBService.engine, future=True)
        statement = select(VPN).filter_by(vpn_config_id=vpn_config_id)
        result = session.execute(statement).scalars().all()
        if result is None:
            return None

        return result

    @staticmethod
    def vpn_delete(vpn_id):
        with Session(DBService.engine) as session:
            session.query(VPN).filter(VPN.vpn_id == vpn_id).delete()
            session.commit()

    @staticmethod
    def migration():
        if not DBService._table_has_column("vpn", "vpn_config_id"):
            column = Column('vpn_config_id', Integer)
            DBService.add_column(DBService.engine, "vpn", column, default=1)

    @staticmethod
    def _table_has_column(table, column):
        engine = DBService.engine
        insp = reflection.Inspector.from_engine(engine)
        has_column = False
        for col in insp.get_columns(table):
            if column not in col['name']:
                continue
            has_column = True
        return has_column

    @staticmethod
    def add_column(engine, table_name, column, default):
        column_name = column.compile(dialect=engine.dialect)
        column_type = column.type.compile(engine.dialect)
        engine.execute('ALTER TABLE %s ADD COLUMN %s %s DEFAULT(%s)' % (table_name, column_name, column_type, default))

    @classmethod
    def vpn_by_vpn_id(cls, vpn_id) -> Optional[VPN]:
        session = Session(DBService.engine, future=True)
        # with Session(DBService.engine) as session:
        statement = select(VPN).filter_by(vpn_id=vpn_id)
        result = session.execute(statement).scalars().first()
        if result is None:
            return None

        return result
