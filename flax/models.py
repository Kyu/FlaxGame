from random import (
    randrange,
    choice
)
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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker
)
from sqlalchemy.sql import (
    func,
    expression
)
from zope.sqlalchemy import register

DBSession = scoped_session(
    sessionmaker(expire_on_commit=False))
register(DBSession)

Base = declarative_base()

TEAMS = {'Black': '2.9', 'Red': '2.2', 'Blue': '9.9', 'Yellow': '9.2'}
SQUAD_TYPES = 'Infantry', 'Tank',  # 'Artillery', 'Heli', 'Kaiamkazee'
SQUAD_TYPES_2 = ['Infantry', 'Infantry', 'Infantry', 'Infantry', 'Infantry', 'Infantry', 'Infantry',
                 'Tank', 'Tank',  'Tank']
CAPITALS = ['2.9', '9.9', '2.2', '9.2']
CITIES = ['6.6', '5.5', '6.9', '5.2']


# Classes to represent each table
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(256), unique=True, nullable=True)
    ip = Column(String(257))
    password = Column(String(256), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    verification = Column(String(256), nullable=True)
    is_verified = Column(Boolean, nullable=False, server_default=expression.false())
    admin = Column(Boolean, nullable=False, server_default=expression.false())


class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    squad_type = Column(String(20), nullable=False)
    team = Column(String(20), nullable=False)
    troops = Column(Integer, default=50)
    location = Column(String(20), nullable=False)

    is_active = Column(Boolean, server_default=expression.true())
    last_active = Column(DateTime, server_default=func.now(), onupdate=func.current_timestamp())
    is_new = Column(Boolean, server_default=expression.true())
    uses_ip = Column(Boolean, server_default=expression.false())

    banned = Column(Boolean, server_default=expression.false())
    banned_by = Column(String(20))
    time_banned = Column(DateTime)
    reason_banned = Column(String(1000))

    actions = Column(Integer, default=10)
    ammo = Column(Integer, default=200)
    morale = Column(Integer, default=100)
    dug_in = Column(Integer, default=0)

    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    management = Column(Integer, default=1)
    attack = Column(Integer, default=1)  # For better defense
    defense = Column(Integer, default=1)  # For better attack
    charisma = Column(Integer, default=1)  # For more troops gained per recruit
    rallying = Column(Integer, default=1)  # For increasing morale
    pathfinder = Column(Integer, default=1)  # For the amount of action you use per movement
    logistics = Column(Integer, default=1)  # For less ammo used per attack
    development = Column(Integer, default=1)  # For less actions used per upgrade


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


class Log(Base):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True)
    logger = Column(String(256))  
    level = Column(String(256))  
    trace = Column(String(535))
    msg = Column(String(535))
    created_at = Column(DateTime, default=func.now())


# Called when checking for permissions. Deny perms go first or are ignored.
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


# Generate hexes from 1.1 - 10.10
def gen_hexes():
    hexes = dict()
    hex_objects = list()

    # Loop makes `hexes` look something like {'1.1': [1, 1], '1.2': [1, 2], '1.3': [1, 3]...} for each x and y
    for x in range(1, 11):
        for y in range(1, 11):
            value = "{0}.{1}".format(x, y)
            if value not in hexes:
                hexes[value] = [x, y]

    # Append each hex to `hex_objects` and give attributes based location type.
    # `type` default = plains, `industry`, `infrastructure` default= 1
    for k, v in hexes.items():
        if k in CAPITALS:
            hex_objects.append(Hex(name=k, x=v[0], y=v[1], type='capital', industry=10, infrastructure=10))
        elif k in CITIES:
            hex_objects.append(Hex(name=k, x=v[0], y=v[1], type='city', industry=5, infrastructure=10))
        else:
            hex_objects.append(Hex(name=k, x=v[0], y=v[1]))
    return hex_objects


def gen_player():
    # Create a player. Choose random team from `TEAMS` and pop into capital.
    # Squad type is chosen randomly from `SQUAD_TYPES`
    # Default start troops are 50. If squad is Tank or Artillery, starter troops are 5
    team = list(TEAMS.keys())[randrange(0, 4)]
    location = TEAMS[team]
    squad = choice(SQUAD_TYPES)  # Make chances unequal
    troops = 50
    if squad in ('Tank', 'Artillery'):
        troops //= 10
    return {'team': team, 'location': location, 'squad': squad, 'troops': troops}
