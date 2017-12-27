import logging
from random import SystemRandom
import string
from smtplib import SMTPRecipientsRefused

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
    # Send email to person.
    # TODO find a way to do this without request param. Also add way to un sub from emails. Also add Fancy emails.
    mailer = request.registry['mailer']
    message = Message(subject=subject, sender='theflaxgame@gmail.com', recipients=[recipient],
                      body=body)
    try:
        mailer.send(message)
    except SMTPRecipientsRefused:
        return "Could not send a verification email to this address, does it exist?"


def hash_string(pw):
    # Returns a hashed string
    return bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())


def matches_hash(_string, hash_string):
    # Return True if hashed `pw` matches `hashed_password`
    return bcrypt.checkpw(_string.encode('utf8'), hash_string.encode('utf8'))


def is_okay_username(username):
    # Username should be between 3 and 16 characters and should not have any special characters except _ . -
    if len(username) < 3 or len(username) > 16:
        return False

    for i in username:
        if i in string.punctuation and i not in "_-.":
            return False

    return True


def is_okay_password(password):
    # See if password matches criteria of 8-64 chars
    if len(password) < 8 or len(password) > 64:
        return False

    return True


def gen_security_code(size=16, chars=string.ascii_letters + string.digits):
    code = ''.join(SystemRandom().choice(chars) for _ in range(size))
    return code  # return hash_string(code)


def verify_security_code(code):
    if not code:
        return "Account already verified!"
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


def create_ip_user(request):
    user = dict(username='', status='')
    if 'username' not in request.params:
        user['status'] = "Username not defined"
        return user
    username = request.params['username']
    ip = request.remote_addr

    try:
        DBSession.query(User).filter_by(username=username).one()
        user_exists = True
    except NoResultFound:
        user_exists = False

    try:
        DBSession.query(User).filter_by(ip=ip).one()
        ip_exists = True
    except NoResultFound:
        ip_exists = False
    except MultipleResultsFound:
        user['status'] = "There already exist accounts using this ip"
        return user

    if ip_exists:
        current_ip_user = DBSession.query(User).filter_by(ip=ip).one()
        current_ip_player = DBSession.query(Player).filter_by(username=current_ip_user.username).one()
        if current_ip_player.uses_ip:  # TODO do I REALLY have to do two queries for this?
            if username == current_ip_user.username:
                user['status'] = "Account created Successfully"
                user['username'] = username
            else:
                user['status'] = "This IP already has an account! Log in as {username}!"\
                    .format(username=current_ip_user.username)
            return user

    if user_exists:
        user['status'] = "This username is already taken!"
        return user

    if not is_okay_username(username):
        user['status'] \
            = "Username should be between 3 and 16 characters and should not have any special characters except _ . -"
        return user

    # create_user(username, email='', password='', ip=ip)

    try:
        stats = gen_player()
        with transaction.manager:
            new_user = User(username=username, ip=ip)
            DBSession.add(new_user)
            transaction.commit()
            player_model = Player(id=new_user.id, username=new_user.username, team=stats['team'],
                                  squad_type=stats['squad'], location=stats['location'], troops=stats['troops'],
                                  uses_ip=True)
            DBSession.add_all([player_model])

            user['status'] = "Account created Successfully"
            user['username'] = username
            return user
    except transaction.interfaces.TransactionFailedError as e:
        err = type(e).__name__ + ': ' + str(e)
    except IntegrityError:
        user['status'] = "This username already exists"
        err = ''   # :thinking:
    except Exception as e:
        err = "Unknown Error: {}".format(type(e).__name__ + ': ' + str(e))
        user['status'] = "An error occured"

    msg = "{err} on create_ip_user(username={username}, password=****)" \
        .format(err=err, username=username)
    log.warning(msg)

    return user


# TODO Refactor to make sure empty passwords don't get entered with IP registration
# Create_full_user
def create_user(username, email, password, request=None):
    # Creates a new User and a Player to match
    # team, squad_type are random
    to_create = {'status': '', 'username': ''}
    if not username:
        to_create['status'] = "Enter a username"
    elif not email:
        to_create['status'] = "Enter an email"
    elif not password:
        to_create['status'] = "Enter a password"
    else:
        if not is_okay_username(username):
            to_create['status'] = \
                "Username should be between 3 and 16 characters and should not have any special characters except _ . -"
        if not is_okay_password(password):
            to_create['status'] = "Your password needs to be 8-64 characters long"

    def mailinator(code):
        if request:
            subject = "Welcome to Flax!"
            recipient = email
            body = 'Welcome to Flax, {username}\nVerify with {host}/verify?code={code})'\
                .format(username=username, host=request.host_url, code=code)
            send_email(request, recipient, subject, body)
            # TODO Test every error that can rise from this.

    def continue_creating(taken=False):
        code = gen_security_code()
        if taken:
            DBSession.query(User).filter_by(username=username).update({'email': email,
                                                                       'password': hash_string(password),
                                                                       'verification': code})
            DBSession.query(Player).filter_by(username=username).update({'uses_ip': False})
            mailinator(code)
            to_create['status'] = "Account officially made official!"
            to_create['username'] = username
            return
        else:
            try:
                if request:
                    ip = request.remote_addr
                else:
                    ip = ''
                stats = gen_player()
                with transaction.manager:
                    code = gen_security_code()
                    new_user = User(username=username, email=email, password=hash_string(password), verification=code,
                                    ip=ip)

                    mailinator(code)
                    DBSession.add(new_user)
                    transaction.commit()
                    player_model = Player(id=new_user.id, username=new_user.username, team=stats['team'],
                                          squad_type=stats['squad'], location=stats['location'], troops=stats['troops'])
                    DBSession.add_all([player_model])
                    to_create['status'] = "Account created Successfully"
                    to_create['username'] = username
                    return
            except transaction.interfaces.TransactionFailedError as e:
                err = type(e).__name__ + ': ' + str(e)
            except IntegrityError:
                to_create['status'] = "This username or email already exists"
                return
            except Exception as e:
                err = "Unknown Error: {0}".format(type(e).__name__ + ': ' + str(e))
        msg = "{err} on create_user(username={username}, email={email}, password=****)" \
            .format(err=err, username=username, email=email)
        log.warning(msg)

    if to_create['status']: # If account creation has already failed
        return to_create

    try:
        prospective_user = DBSession.query(User).filter_by(username=username).one()
    except NoResultFound:
        # If username not found
        continue_creating()
        return to_create
    else:
        # Username already exists, checking to see if logged in as taken username
        if prospective_user.username != request.authenticated_userid:
            to_create['status'] = "Username already taken!"
            return to_create
        else:
            continue_creating(taken=True)
            return to_create   # This establishes an already existing user with an email and password. 
            # taken=True does not attempt to catch errors

    return to_create


def verify_login(username, password):
    # Verifies a login (username is interchangeable with email)
    usr = dict(username='', status='')
    if not username:
        usr['status'] = "Enter a username"
    elif not password:
        usr['status'] = "Enter a password"
    else:
        try:
            expected_user = DBSession.query(User).filter(or_(User.username == username, User.email == username)).one()
            expected_password = expected_user.password
            if matches_hash(password, expected_password):
                usr['username'] = expected_user.username
                usr['status'] = "Logged in successfully"
                DBSession.query(Player).filter_by(username=username).update({Player.is_active: True})
                return usr
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

    DBSession.query(User).filter_by(username=username).update({'password': hash_string(new)})


def start_recovery(request, email):
    try:
        user = DBSession.query(User).filter_by(email=email)
        usr = user.one()
    except NoResultFound:
        return "Email does not exist in database!"

    with transaction.manager:
        code = gen_security_code()
        user.update({'verification': code})

        body = 'Hello, {name}To recover your password, please visit this link: {host}/recover?code={code}'\
            .format(name=usr.username, host=request.host_url, code=code)
        msg = send_email(request, usr.email, "Flax password recovery", body)
        transaction.commit()
        if msg is not None:
            return msg
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
        return ("Password does not meet criteria, please review! Remember: Your password needs: "
                "To be at least 6 characters long, 1 upper and 1 lowercase letter, 1 number, and one special character")

    user.update({'password': hash_string(new), 'verification': ''})
    return "Password changed successfully"


def change_setting(username, password, setting, new):
    # Change settings, user has to verify pw each time
    if not verify_login(username, password):
        return "Invalid credentials!"

    valid_settings = ['email', 'password']

    if setting not in valid_settings:
        return "Invalid setting!"
    if setting == 'password':
        new = hash_string(new)
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
        pass
    except Exception as e:
        msg = "{err} on change_setting(userid={userid}, request={request})".format(
            err=str(type(e).__name__ + ': ' + str(e)), userid=userid, request=request)
        log.warning(msg)
        pass

    return result
