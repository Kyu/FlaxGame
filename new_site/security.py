import transaction
from datetime import datetime

import bcrypt

from sqlalchemy import or_

from sqlalchemy.orm.exc import NoResultFound

from sqlalchemy.exc import IntegrityError

from .models import (
    Captain,
    User,
    DBSession,
)


def hash_password(pw):
    return bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
    # THIS IS A STRING :: return pwhash.decode('utf8')


def check_password(pw, hashed_pw):
    return bcrypt.checkpw(pw.encode('utf8'), hashed_pw.encode('utf8'))


def create_user(username, email, password):
    try:
        with transaction.manager:
            new_user = User(username=username, email=email, hash_string=hash_password(password),
                            created_at=datetime.utcnow())
            DBSession.add(new_user)
            transaction.commit()
            # Location, team should be random
            player_model = Captain(uid=new_user.uid, username=new_user.username, team='Black', 
                                   experience=1, level=1, troops=50, location=2.2, last_active=datetime.utcnow())
            DBSession.add(player_model)
            return True
    except transaction.interfaces.TransactionFailedError:
        pass
    except IntegrityError:
        pass
    except Exception as e:
        print(type(e).__name__ + ': ' + str(e))
    
    return False


def verify_login(username, password):
    usr = {}
    try:
        expected_user = DBSession.query(User).filter(or_(User.username == username, User.email == username)).one()
        expected_password = expected_user.hash_string
        if check_password(password, expected_password):
            usr['username'] = expected_user.username
    except NoResultFound:
        pass
    except Exception as e:
        print(type(e).__name__ + ': ' + str(e))
        
    return usr


def groupfinder(userid, request):
    result = []
    try:
        team = DBSession.query(Captain).filter_by(username=userid).one().team
        result.append("group:{}".format(team))
    except NoResultFound:
        pass
    except Exception as e:
        print(type(e).__name__ + ': ' + str(e))
    
    return result
