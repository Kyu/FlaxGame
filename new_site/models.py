from pyramid.security import Allow, Everyone

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime
)

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker
)

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(
    sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    uid = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True)
    email = Column(String(256), unique=True)
    hash_string = Column(String(256))
    created_at = Column(DateTime)


class Captain(Base):
    __tablename__ = 'captain'
    uid = Column(Integer, primary_key=True, autoincrement=False)
    username = Column(String(20))
    team = Column(String(20))
    experience = Column(Integer)
    level = Column(Integer)
    troops = Column(Integer)
    location = Column(Float)
    '''insert attributes and shit here'''
    last_active = Column(DateTime)


class Root(object):
    __acl__ = [(Allow, Everyone, 'view'),
               (Allow, 'group:Black', 'edit')]

    def __init__(self, request):
        pass
"""
class Team(Base):
    __tablename__ = 'team'
    name = Column(String(20))
    colour = Column(String(20))






class General(Base):
    '''Everyone past lvl 10 becomes a General, if there are more than 2, a vote ensues'''
    __tablename__ = 'general'
    uid = Column(Integer, primary_key=True, autoincrement=False)
    username = Column(String(20))
    team = Column(String(20))
    votes = Column(String(20))
"""
'''add table for portraits next'''
