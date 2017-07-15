from pyramid.security import Allow, Everyone

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
)
from sqlalchemy.sql import func

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
    username = Column(String(20), unique=True)
    email = Column(String(256), unique=True)
    password = Column(String(256))
    created_at = Column(DateTime, server_default=func.now())
    is_verified = Column(Boolean, default=False)
    admin = Column(Boolean, default=False)


class Player(Base):
    __tablename__ = 'players'
    uid = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True)
    squad_type = Column(String(20))
    team = Column(String(20))
    troops = Column(Integer, default=50)
    location = Column(String(20))

    is_active = Column(Boolean, default=True)
    last_active = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_new = Column(Boolean, default=True)

    actions = Column(Integer, default=10)
    ammo = Column(Integer, default=200)
    morale = Column(Integer, default=100)

    # TODO development stat for upgrading?
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    attack = Column(Integer, default=1)  # For better defense
    defense = Column(Integer, default=1)  # For better attack
    charisma = Column(Integer, default=1)  # For more troops gained per recruit
    rallying = Column(Integer, default=1)  # For increasing morale
    pathfinder = Column(Integer, default=1)  # For the amount of action you use per movement
    logistics = Column(Integer, default=1)  # For less ammo used per attack


class Hex(Base):
    __tablename__ = 'hexes'
    name = Column(String(20), primary_key=True)
    x = Column(Integer)
    y = Column(Integer)
    controlled_by = Column(String(20))
    redcontrol = Column(Integer)
    bluecontrol = Column(Integer)
    blackcontrol = Column(Integer)
    yellowcontrol = Column(Integer)
    ammo = Column(Integer, default=100)
    population = Column(Integer, default=10)
    industry = Column(Integer, default=10)
    infrastructure = Column(Integer, default=5)


class Team(Base):
    __tablename__ = 'teams'
    name = Column(String(20), primary_key=True)
    capital = Column(String(20))


# TODO `Deny` perms for banned people?
class Root(object):
    __acl__ = [(Allow, Everyone, 'view'),
               (Allow, 'group:Black', 'play'),
               (Allow, 'group:Yellow', 'play'),
               (Allow, 'group:Red', 'play'),
               (Allow, 'group:Blue', 'play')]

    def __init__(self, request):
        pass


"""
class Team(Base):
    __tablename__ = 'team'
    name = Column(String(20))
    colour = Column(String(20))
"""
'''add table for portraits next'''
