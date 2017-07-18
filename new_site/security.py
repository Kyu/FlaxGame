import transaction
from random import randrange
import logging

import bcrypt

from sqlalchemy import or_

from sqlalchemy.orm.exc import NoResultFound

from sqlalchemy.exc import IntegrityError

from .models import (
    Player,
    User,
    DBSession,
)

log = logging.getLogger(__name__)
teams = {'Black': '2.9', 'Red':'2.2', 'Blue': '9.9', 'Yellow': '9.2'}


def hash_password(pw):
    return bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
    # THIS IS A STRING :: return pwhash.decode('utf8')


def check_password(pw, hashed_pw):
    return bcrypt.checkpw(pw.encode('utf8'), hashed_pw.encode('utf8'))


def create_user(username, email, password):
    if not username:
        return "Enter a username"
    elif not email:
        return "Enter an email"
    elif not password:
        return "Enter a password"
    else:
        try:
            team = list(teams.keys())[randrange(0, 4)]
            location = teams[team]
            with transaction.manager:
                new_user = User(username=username, email=email, password=hash_password(password))
                DBSession.add(new_user)
                transaction.commit()
                # Location, team should be random
                player_model = Player(uid=new_user.uid, username=new_user.username, team=team, squad_type="Captain",
                                      location=location)
                DBSession.add(player_model)

                return "Account created Sucessfully"
        except transaction.interfaces.TransactionFailedError as e:
            return "Error: {}".format(type(e).__name__ + ': ' + str(e))
        except IntegrityError:
            return "This username or email already exists"
        except Exception as e:
            return "Unknown Error: {}".format(type(e).__name__ + ': ' + str(e))

    return "?????"


def verify_login(username, password):
    usr = {}
    if not username:
        usr['status'] = "Enter a username"
    elif not password:
        usr['status'] = "Enter a password"
    else:
        try:
            expected_user = DBSession.query(User).filter(or_(User.username == username, User.email == username)).one()
            expected_password = expected_user.password
            if check_password(password, expected_password):
                usr['username'] = expected_user.username
        except NoResultFound:
            pass
        except Exception as e:
            print(type(e).__name__ + ': ' + str(e))
        usr['status'] = "Login Failed"
    return usr


def change_setting(username, password, setting, new):
    if not verify_login(username, password):
        return "Invalid credentials!"

    valid_settings = ['email', 'password']

    if setting not in valid_settings:
        return "Invalid setting!"
    if setting == 'password':
        new = hash_password(new)
    try:
        with transaction.manager:
            DBSession.query(User).filter_by(username=username).update({setting: new})
        return "{} changed sucessfully!".format(setting)
    except Exception as e:
        msg = "{err} on change_setting(username={username}, password=****, setting='{setting}', new={new})".format(
            err=str(type(e).__name__ + ': ' + str(e)), username=username, setting=setting, new=new)
        log.warning(msg)
        return "An error occurred"


def groupfinder(userid, request):
    result = []
    try:
        team = DBSession.query(Player).filter_by(username=userid).one().team
        result.append("group:{}".format(team))
    except NoResultFound:
        pass
        return
    except Exception as e:
        print(type(e).__name__ + ': ' + str(e))
        return
    return result
