from pyramid.security import (
    Allow,
    Deny,
    Everyone
)

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
)
from sqlalchemy.sql import (
    func,
    expression
)

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker
)

from zope.sqlalchemy import ZopeTransactionExtension


DBSession = scoped_session(
    sessionmaker(extension=ZopeTransactionExtension(), expire_on_commit=False))

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    uid = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(256), unique=True, nullable=False)
    password = Column(String(256), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    is_verified = Column(Boolean, nullable=False, server_default=expression.false())
    admin = Column(Boolean, nullable=False, server_default=expression.false())


class Player(Base):
    __tablename__ = 'players'
    uid = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    squad_type = Column(String(20), nullable=False)
    team = Column(String(20), nullable=False)
    troops = Column(Integer, default=50)
    location = Column(String(20), nullable=False)

    is_active = Column(Boolean, server_default=expression.true())
    last_active = Column(DateTime, server_default=func.now(), onupdate=func.current_timestamp())
    is_new = Column(Boolean, server_default=expression.true())

    banned = Column(Boolean, server_default=expression.false())
    time_banned = Column(DateTime)
    reason_banned = Column(String(1000))

    actions = Column(Integer, default=10)
    ammo = Column(Integer, default=200)
    morale = Column(Integer, default=100)

    # TODO development stat for upgrading?
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    management = Column(Integer, default=1)
    attack = Column(Integer, default=1)  # For better defense
    defense = Column(Integer, default=1)  # For better attack
    charisma = Column(Integer, default=1)  # For more troops gained per recruit
    rallying = Column(Integer, default=1)  # For increasing morale
    pathfinder = Column(Integer, default=1)  # For the amount of action you use per movement
    logistics = Column(Integer, default=1)  # For less ammo used per attack


class Hex(Base):
    __tablename__ = 'hexes'
    name = Column(String(20), primary_key=True)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    type = Column(String(20), server_default='plains')
    control = Column(String(20), server_default='None')
    red = Column(Integer, default=0)
    blue = Column(Integer, default=0)
    black = Column(Integer, default=0)
    yellow = Column(Integer, default=0)
    ammo = Column(Integer, default=50)
    population = Column(Integer, default=30)
    industry = Column(Integer, default=1)
    infrastructure = Column(Integer, default=1)


class Team(Base):
    __tablename__ = 'teams'
    name = Column(String(20), nullable=False, primary_key=True)
    capital = Column(String(20), nullable=False)


class Radio(Base):
    __tablename__ = 'radio'
    id = Column(Integer, primary_key=True, autoincrement=True)
    author = Column(String(20), nullable=False)
    message = Column(String(500), nullable=False)
    team = Column(String(20), nullable=False)
    timestamp = Column(DateTime, server_default=func.current_timestamp())
    active = Column(Boolean, server_default=expression.true())


# TODO `Deny` perms for banned people?
class Root(object):
    __acl__ = [(Deny, 'group:Banned', 'play'),
               (Allow, Everyone, 'view'),
               (Allow, 'group:Black', 'play'),
               (Allow, 'group:Yellow', 'play'),
               (Allow, 'group:Red', 'play'),
               (Allow, 'group:Blue', 'play'),
               (Allow, 'group:Admin', 'admin'), ]

    def __init__(self, request):
        pass


"""
class Team(Base):
    __tablename__ = 'team'
    name = Column(String(20))
    colour = Column(String(20))
"""
'''add table for portraits next'''
