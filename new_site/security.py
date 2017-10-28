import logging
from random import randrange, SystemRandom
import string

import bcrypt
import transaction
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from pyramid_mailer.message import Message

from .models import (
    Player,
    User,
    DBSession,
    gen_player
)

log = logging.getLogger(__name__)


def send_email(request, recipient, subject, body):
    mailer = request.registry['mailer']
    message = Message(subject=subject, sender='theflaxgame@gmail.com', recipients=[recipient],
                      body=body)
    mailer.send(message)


def hash_password(pw):
    # Returns hashed password as string
    return bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())


def check_password(pw, hashed_pw):
    # Return True if hashed `pw` matches `hashed_password`
    return bcrypt.checkpw(pw.encode('utf8'), hashed_pw.encode('utf8'))


def is_okay_username(username):
    # Username should be between 3 and 16 characters and should not have any special characters except _ . -
    if len(username) < 3 or len(username) > 16:
        return False

    for i in username:
        if i in string.punctuation and i not in "_-.":
            return False

    return True


def is_okay_password(password):
    if len(password) < 6:
        return False

    cap, low, num, spec = False, False, False, False
    for i in password:
        if i.isupper():
            cap = True
        elif i.islower():
            low = True
        elif i.isdigit():
            num = True
        # elif i in string.punctuation:
            # spec = True

    return cap and low and num  # and spec


def gen_security_code(size=16, chars=string.ascii_letters+ string.digits):
    return ''.join(SystemRandom().choice(chars) for _ in range(size))


def verify_security_code(code):
    try:
        with transaction.manager:
            user = DBSession.query(User).filter_by(verification=code)
            user.one()  # If user doesn't exist, raises NoResultFound
            user.update({'is_verified': True, 'verification': ''})
        return "Successfully verified email!"
    except NoResultFound:
        return "This verification code has either expired or does not exist!"
    except Exception as e:
        msg = "{err} on verify_security_code(code=****)".format(
            err=str(type(e).__name__ + ': ' + str(e)))
        log.warning(msg)
        return "An error occurred"


def create_user(username, email, password, request=None):
    # Creates a new User and a Player to match
    # team, squad_type are random
    if not username:
        return "Enter a username"
    elif not email:
        return "Enter an email"
    elif not password:
        return "Enter a password"
    else:
        if not is_okay_username(username):
            return "Username should be between 3 and 16 characters and should not have any special characters except _ . -"
        if not is_okay_password(password):
            return "Your password needs: To be atleast 6 characters long, 1 upper and 1 lowercase letter, 1 number, and one special character"
        try:
            stats = gen_player()
            with transaction.manager:
                code = gen_security_code()
                new_user = User(username=username, email=email, password=hash_password(password), verification=code)
                DBSession.add(new_user)
                if request:
                    subject = "Welcome to Flax!"
                    recipient = email
                    body = 'Start playing now!\nVerify with http://localhost:6543/verify?code=' + code
                    send_email(request, recipient, subject, body)

                transaction.commit()
                player_model = Player(id=new_user.id, username=new_user.username, team=stats['team'],
                                      squad_type=stats['squad'], location=stats['location'], troops=stats['troops'])
                DBSession.add_all([player_model])

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
            DBSession.query(Player).filter_by(username=username).update({Player.is_active: True})
        except NoResultFound:
            pass
        except Exception as e:
            msg = "{err} on verify_login(username={username}, password=****)"\
                .format(err=type(e).__name__ + ': ' + str(e), username=username)
            log.warning(msg)
        usr['status'] = "Login Failed"
    return usr


def change_password(username, new, old, force=False):
    if not force:
        verified = verify_login(username, old)
    else:
        verified = True

    if not verified:
        return "Could not verify old credentials"

    DBSession.query(User).filter_by(username=username).update({'password': hash_password(new)})


def start_recovery(request, email):
    try:
        user = DBSession.query(User).filter_by(email=email)
        usr = user.one()
    except NoResultFound:
        return "Email does not exist in database!"

    with transaction.manager:
        code = gen_security_code()
        user.update({'verification': code})

        body = 'To recover your password, please visit this link: http://localhost:6543/recover?code=' + code
        send_email(request, usr.email, "Flax password recovery", body)
        transaction.commit()
    return "A recovery email has been sent!"


def recover_password(new, code):
    try:
        user = DBSession.query(User).filter_by(verification=code)
        usr = user.one()
    except NoResultFound:
        return "Invalid or expired verification1"
    except MultipleResultsFound:
        return "Invalid or expired verification2"

    if not usr.verification == code:
        return "Invalid or expired verification!3"

    if not is_okay_password(new):
        return "Password does not meet criteria, please review! Remember: Your password needs: To be atleast 6 characters long, 1 upper and 1 lowercase letter, 1 number, and one special character"

    user.update({'password': hash_password(new), 'verification': ''})
    return "Password changed successfully"


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
