import logging
from random import randrange

import bcrypt
import transaction
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from .models import (
    Player,
    User,
    Avatar,
    DBSession,
    gen_player
)

log = logging.getLogger(__name__)


def hash_password(pw):
    # Returns hashed password as string
    return bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())


def check_password(pw, hashed_pw):
    # Return True if hashed `pw` matches `hashed_password`
    return bcrypt.checkpw(pw.encode('utf8'), hashed_pw.encode('utf8'))


def create_user(username, email, password):
    # Creates a new User and a Player to match
    # team, squad_type are random
    if not username:
        return "Enter a username"
    elif not email:
        return "Enter an email"
    elif not password:
        return "Enter a password"
    else:
        try:
            stats = gen_player()
            with transaction.manager:
                new_user = User(username=username, email=email, password=hash_password(password))
                DBSession.add(new_user)
                transaction.commit()
                player_model = Player(id=new_user.id, username=new_user.username, team=stats['team'],
                                      squad_type=stats['squad'], location=stats['location'], troops=stats['troops'])
                avatar = Avatar(id=new_user.id, default=randrange(0, 3))
                DBSession.add_all([player_model, avatar])

                return "Account created Successfully"
        except transaction.interfaces.TransactionFailedError as e:
            err = type(e).__name__ + ': ' + str(e)
        except IntegrityError:
            return "This username or email already exists"
        except Exception as e:
            err = "Unknown Error: {}".format(type(e).__name__ + ': ' + str(e))

    msg = "{err} on verify_login(username={username}, email={email}, password=****)" \
        .format(err=err, username=username, email=email)
    log.warning(msg)

    return err


def verify_login(username, password):
    # Verifies a login (username is interchangeable with email)
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
            msg = "{err} on verify_login(username={username}, password=****)"\
                .format(err=type(e).__name__ + ': ' + str(e), username=username)
            log.warning(msg)
        usr['status'] = "Login Failed"
    return usr


def change_setting(username, password, setting, new):
    # Change settings, user has to verify pw each time
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
        return "{} changed successfully!".format(setting)
    except Exception as e:
        msg = "{err} on change_setting(username={username}, password=****, setting='{setting}', new={new})".format(
            err=str(type(e).__name__ + ': ' + str(e)), username=username, setting=setting, new=new)
        log.warning(msg)
        return "An error occurred"


def groupfinder(userid, request):
    # Returns the groups relevant to a player, pyramid then refers to .models.Root for permissions
    result = []
    try:
        player = DBSession.query(Player).filter_by(username=userid).one()
        if player.banned:
            result.append("group:Banned")
        result.append("group:{}".format(player.team))
        user = DBSession.query(User).filter_by(id=player.id).one()
        if user.admin:
            result.append("group:Admin")
    except NoResultFound:
        return
    except Exception as e:
        msg = "{err} on change_setting(userid={userid}, request={request})".format(
            err=str(type(e).__name__ + ': ' + str(e)), userid=userid, request=request)
        log.warning(msg)
        return

    return result
