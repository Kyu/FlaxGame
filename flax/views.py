from pyramid.httpexceptions import (
    HTTPFound,
    HTTPForbidden
)
from pyramid.response import Response
from pyramid.security import (
    remember,
    forget
)
from pyramid.view import (
    view_config,
    forbidden_view_config,
    notfound_view_config
)

from .admin import (
    ban_player,
    unban_player,
    get_user,
    hide_announcement
)
from .game import (
    get_all_game_info_for,
    get_player_info,
    send_player_to,
    player_attack,
    get_team_info,
    level_up_player,
    xp_for_level_up,
    give_player_ammo,
    increase_player_troops,
    upgrade_hex_for,
    upgrade_infrastructure_for,
    get_radio_for,
    send_message,
    player_dig_in
)
from .security import (
    create_user,
    verify_login,
    change_setting,
    verify_security_code,
    start_recovery,
    recover_password,
    create_ip_user
)


def return_to_sender(request):
    try:
        if request.referer == request.url or not request.referrer:
            return '/'
        return request.referer
    except AttributeError:
        return '/'


@view_config(route_name='home', renderer='templates/default.pt')
def home(request):
    if request.authenticated_userid:
        return HTTPFound(request.route_url('game'))

    resp = {'page_title': 'GAMENAMEHERE - DESCRIPTION', 'name': request.authenticated_userid}
    return resp


@forbidden_view_config(renderer='templates/403.pt')
def view_forbidden(request):
    if request.authenticated_userid:
        player = get_player_info(request.authenticated_userid)
        return {'player': player, 'banned': player.banned}
    return {'player': {}}


@notfound_view_config(renderer='templates/404.pt')
def not_found(request):
    return {}


@view_config(route_name='test_view', renderer='templates/test.pt', permission='admin')
def test_view(request):
    return {'page_title': 'Test View'}


@view_config(route_name='register', renderer='templates/register.pt')
def register(request):
    player = None
    if request.authenticated_userid and request.method != 'POST':
        player = get_player_info(request.authenticated_userid)
        if player.uses_ip:  # TODO Add IP to admin thingy
            pass
        else:
            return HTTPFound(location='/')

    if request.method == 'POST':
        if 'register' in request.params:
            if 'username' not in request.params:
                message = request.session.flash("No username defined")
            elif 'password' not in request.params:
                message = request.session.flash("Enter a password")
            elif 'email' not in request.params:
                message = request.session.flash("Enter an email address")
            else:
                username = request.params['username']
                password = request.params['password']
                email = request.params['email']
                if email and password and username:
                    message = create_user(username, email, password, request)
                else:
                    message = "All fields must be filled!"
            request.session.flash(message, 'register')

        return HTTPFound(location=request.route_url('register'))
    else:
        return {'player': player}


@view_config(route_name='login', request_method='POST')
def login(request):
    message = ''
    if 'login' in request.params:
        if 'username' not in request.params:
            request.session.flash("No username defined")
        elif 'password' not in request.params:
            request.session.flash("Enter a password")
        else:
            username = request.params['username']
            password = request.params['password']
            verified = verify_login(username, password)
            if 'username' in verified:
                headers = remember(request, verified['username'])
                return HTTPFound(location=return_to_sender(request), comment='Logged in successfully', headers=headers)
            else:
                message = verified['status']

        request.session.flash(message, 'login')

    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='ip_login', request_method='POST')
def ip_login(request):
    msg = create_ip_user(request)
    request.session.flash(msg, 'oneclick')
    if msg == 'Account created Successfully':
        headers = remember(request, request.params['username'])
        return HTTPFound(location=return_to_sender(request), comment='Logged in successfully', headers=headers)

    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='verify')  # Maybe create another table for this?
def verify(request):
    code = request.params['code']
    verification_attempt = verify_security_code(code)
    request.session.flash(verification_attempt, 'login')
    return HTTPFound(location='/')


@view_config(route_name='recover_password', renderer='templates/recover.pt')
def recover_password_view(request):
    code = request.params.get('code')

    if request.method == 'POST':
        if 'startprocess' in request.params:
            action = start_recovery(request=request, email=request.params['email'])
            request.session.flash(action, 'recovery')
        elif 'changepass' in request.params:
            action = recover_password(new=request.params['password'], code=code)
            request.session.flash(action, 'recovery')

    return {'code': code}


@view_config(route_name='logout')
def logout(request):
    if not request.authenticated_userid:
        return HTTPForbidden()
    headers = forget(request)
    return HTTPFound(location='/', headers=headers)
    # return Response(json_body={'logged_out': True}, headers=headers)


@view_config(route_name='game', renderer='templates/game.pt', permission='play')
def game(request):
    username = request.authenticated_userid
    info = get_all_game_info_for(username)
    return {'hexes': info['hexes'], 'player': info['player'], 'user': get_user(username), 'current_hex': '',
            'radio': get_radio_for(username)}


@view_config(route_name='hex_view', renderer='templates/game.pt', permission='play')
def hex_view(request):
    hex_name = request.matchdict['name']
    username = request.authenticated_userid
    info = get_all_game_info_for(username, location=hex_name)
    if not info:
        return HTTPFound(location=request.route_url('home'))

    return {'hexes': info['hexes'], 'current_hex': info['current_hex'], 'currently_here': info['currently_here'],
            'player': info['player'], 'user': get_user(username), 'movable': info['movable'],
            'radio': get_radio_for(username)}


@view_config(route_name='move_to', renderer='templates/game.pt', request_method='POST', permission='play')
def move_to(request):
    if 'position' in request.params:
        location = request.params['position']
        movement = send_player_to(location, request.authenticated_userid)
        request.session.flash(movement, 'action')

    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='attack_player', renderer='templates/game.pt', request_method='POST', permission='play')
def attack_player(request):
    if 'player_called' in request.params:
        attacker, defender = request.authenticated_userid, request.params['player_called']
        attack = player_attack(attacker=attacker, defender=defender)
        request.session.flash(attack, 'action')

    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='get_ammo', request_method='POST', permission='play')
def increase_ammo(request):
    increase = give_player_ammo(request.authenticated_userid)
    request.session.flash(increase, 'action')

    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='recruit', request_method='POST', permission='play')
def recruit(request):
    increase = increase_player_troops(request.authenticated_userid)
    request.session.flash(increase, 'action')

    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='upgrade_industry', request_method='POST', permission='play')
def increase_hex_industry(request):
    increase = upgrade_hex_for(request.authenticated_userid)
    request.session.flash(increase, 'action')

    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='upgrade_infrastructure', request_method='POST', permission='play')
def increase_hex_infrastructure(request):
    increase = upgrade_infrastructure_for(request.authenticated_userid)
    request.session.flash(increase, 'action')

    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='dig_in', request_method='POST', permission='play')
def dig_in(request):
    dig = player_dig_in(request.authenticated_userid)
    request.session.flash(dig, 'action')
    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='team_info', renderer='templates/team.pt', permission='play')
def team_info(request):
    team_name = request.matchdict['team']
    info = get_team_info(team_name)
    if info:
        return {'team': info, 'player': get_player_info(request.authenticated_userid)}
    return HTTPFound(location=request.route_url('home'),
                     comment="Team not found: {team_name}".format(team_name=team_name))


@view_config(route_name='send_message', request_method='POST', permission='play')
def broadcast_message(request):
    if 'message' in request.params:
        msg = send_message(_from=request.authenticated_userid, message=request.params['message'])
        request.session.flash(msg, 'radio')

    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='profile', renderer='templates/profile.pt', permission='play')
def profile_page(request):
    player = get_player_info(request.authenticated_userid)

    return {'player': player, 'xp_need': xp_for_level_up(player)}


@view_config(route_name='level_up', request_method='POST', permission='play')
def level_up(request):
    player = get_player_info(request.authenticated_userid)
    if 'attribute' in request.params:
        lvl_up = level_up_player(player, request.params['attribute'])
        request.session.flash(lvl_up)

    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='change_setting', request_method='POST', permission='play')
def change_setting_view(request):
    user = request.authenticated_userid
    if 'password' not in request.params:
        request.session.flash("Enter a password!")
    elif 'new_value' not in request.params:
        request.session.flash("Enter a new value!")
    elif 'setting' in request.params:
        alter = change_setting(username=user, password=request.params['password'], setting=request.params['setting'],
                               new=request.params['new_value'])
        request.session.flash(alter)
        return HTTPFound(location=return_to_sender(request),
                         comment='{} changed successfully'.format(request.params['setting']))

    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='admin', renderer='templates/admin.pt', permission='admin')
def admin_view(request):
    resp = {'name': request.authenticated_userid}
    return resp


@view_config(route_name='ban_player', request_method='POST', permission='admin')
def ban_player_view(request):
    banner = request.authenticated_userid
    reason = request.params['reason']
    username = request.params['username']
    time = request.params['until']

    ban = ban_player(username, reason, banner, until=time)
    request.session.flash(ban, 'ban_info')
    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='unban_player', request_method='POST', permission='admin')
def unban_player_view(request):
    unb = unban_player(request.params['username'])
    request.session.flash(unb, 'unban_info')
    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='player_info', permission='admin')
def player_info_view(request):
    args = ['id', 'username', 'squad_type', 'team', 'troops', 'location', 'dug_in', 'last_active', 'actions', 'ammo', 'level',
            'banned', 'banned_by', 'time_banned', 'reason_banned']
    zeroes = 'actions, ammo', 'banned', 'dug_in'
    player = get_player_info(request.params['username'])
    if not player:
        pinfo = "Invalid player: {}".format(request.params['username'])
        request.session.flash(pinfo, 'player_info')
    else:
        prep = ["{0}: {1}".format(arg, getattr(player, arg)) for arg in args if (getattr(player, arg) or (not getattr(player, arg) and arg in zeroes))]
        for i in prep:
            request.session.flash(i, 'player_info')

    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='broadcast', request_method='POST', permission='admin')
def send_announcement_view(request):
    msg = request.params['message']
    author = request.authenticated_userid
    sent = send_message(message=msg, broadcast_by=author)
    request.session.flash(sent, 'announcement_info')
    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='hide_broadcast', request_method='POST', permission='admin')
def hide_announcement_view(request):
    _id = request.params['id']
    hide = hide_announcement(_id)
    request.session.flash(hide, 'announcement_info2')
    return HTTPFound(location=return_to_sender(request))
