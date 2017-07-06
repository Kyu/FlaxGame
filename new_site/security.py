import bcrypt

from .models import (
    DBSession,
    Captain
)

def hash_password(pw):
    return bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
    # THIS IS A STRING :: return pwhash.decode('utf8')


def check_password(pw, hashed_pw):
    return bcrypt.checkpw(pw.encode('utf8'), hashed_pw)


USERS = {'editor': hash_password('editor'),
         'viewer': hash_password('viewer')}

GROUPS = {'editor': ['group:editors']}


def groupfinder(userid, request):
    DBSession.query(Captain).filter_by(username=login).one().team

    if userid in USERS:
        return GROUPS.get(userid, [])