import transaction
from datetime import datetime

import bcrypt
'''
from sqlalchemy import or_

from .models import (
    Captain,
    User,
    DBSession,
)
'''

def hash_password(pw):
    return bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
    # THIS IS A STRING :: return pwhash.decode('utf8')


def check_password(pw, hashed_pw):
    return bcrypt.checkpw(pw.encode('utf8'), hashed_pw)


USERS = {'editor': hash_password('editor'),
         'viewer': hash_password('viewer')}

GROUPS = {'editor': ['group:editors']}


def create_user(username, email, password):
    with transaction.manager:
        try:
            new_user = User(username=username, email=email, hash_string=hash_password(password),
                            created_at=datetime.utcnow())
            DBSession.add(new_user)
            transaction.commit()
            # Location, team should be random
            player_model = Captain(uid=new_user.uid, username=new_user.username, team='Black', 
                                   experience=1, level=1, troops=50, location=2.2, last_active=datetime.utcnow())
            DBSession.add(player_model)
            return True
        except Exception as e:
            print(type(e).__name__ + ': ' + str(e))
            return False

'''
def verify_login(username, password):
    try:
        expected_password = DBSession.query(User).filter(or_(User.username == username, User.email == username))
        if check_password(password, expected_password):
            return True
    except Exception as e:  # sqlalchemy.orm.exc.NoResultFound :: when username not found
        print(type(e).__name__ + ': ' + str(e))
        return False


def groupfinder(userid, request):
    try:
        team = DBSession.query(Captain).filter_by(username=userid).one().team
        t_group = "group:{}".format(team)
    except Exception as e:
        print(type(e).__name__ + ': ' + str(e))
        return []
    
    return [t_group]
'''