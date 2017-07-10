from pyramid.security import Allow, Everyone

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    Boolean,
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
    username = Column(String(20), unique=True)
    email = Column(String(256), unique=True)
    password = Column(String(256))
    created_at = Column(DateTime)
    admin = Column(Boolean, default=False)


class Player(Base):
    __tablename__ = 'players'
    uid = Column(Integer, primary_key=True, autoincrement=False)
    username = Column(String(20))
    squad_type = Column(String(20))
    team = Column(String(20))
    experience = Column(Integer)
    level = Column(Integer)
    troops = Column(Integer)
    location = Column(String(20))
    '''insert attributes and shit here'''
    last_active = Column(DateTime)


class Hex(Base):
    __tablename__ = 'hexes'
    name = Column(String(20), primary_key=True)
    x = Column(Integer)
    y = Column(Integer)



class Root(object):
    __acl__ = [(Allow, Everyone, 'view'),
               (Allow, 'group:Black', 'play')]

    def __init__(self, request):
        pass


"""
class Team(Base):
    __tablename__ = 'team'
    name = Column(String(20))
    colour = Column(String(20))
"""
'''add table for portraits next'''
