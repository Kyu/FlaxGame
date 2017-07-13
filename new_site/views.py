from pyramid.httpexceptions import HTTPFound

from pyramid.security import (
    remember, 
    forget
)

from pyramid.view import (
    view_config,
    forbidden_view_config
)

from .security import (
    create_user,
    verify_login
)

from .game import (
    get_all_game_info_for,
    get_player_info,
    send_player_to,
    player_attack,
    get_team_info
)


def return_to_sender(request):
    if request.referer == request.url or not request.referrer:
        return '/'
    return request.referer


@view_config(route_name='home', renderer='templates/default.pt')
@forbidden_view_config(renderer='templates/default.pt')
def home(request):
    if request.authenticated_userid:
        return HTTPFound(request.route_url('game'))

    resp = {'page_title': 'GAMENAMEHERE - DESCRIPTION', 'name': request.authenticated_userid}
    return resp


@view_config(route_name='register', request_method='POST')
def register(request):
    if request.authenticated_userid:
        return HTTPFound(location='/')

    if 'register' in request.params:
        if 'username' not in request.params:
            request.session.flash("No username defined")
        elif 'password' not in request.params:
            request.session.flash("Enter a password")
        elif 'email' not in request.params:
            request.session.flash("Enter an email address")
        else:
            username = request.params['username']
            password = request.params['password']
            email = request.params['email']
            if email and password and username:
                created = create_user(username, email, password)
                request.session.flash(created)

    return HTTPFound(location=request.route_url('home'))


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
                return HTTPFound(location=return_to_sender(request), headers=headers)
            else:
                message = verified['status']

        request.session.flash(message)

    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    url = request.route_url('home')
    return HTTPFound(location=url, headers=headers)


@view_config(route_name='game', renderer='templates/game.pt', permission='play')
def game(request):
    info = get_all_game_info_for(request.authenticated_userid)
    return {'page_title': 'GAMENAMEHERE - DESCRIPTION', 'name': request.authenticated_userid, 'hexes': info['hexes'],
            'player': info['player'], 'current_hex': ''}


@view_config(route_name='hex_view', renderer='templates/game.pt', permission='play')
def hex_view(request):
    hex_name = request.matchdict['name']
    info = get_all_game_info_for(request.authenticated_userid, hex_name)

    return {'page_title': 'GAMENAMEHERE - DESCRIPTION', 'name': request.authenticated_userid, 'hexes': info['hexes'],
            'current_hex': info['current_hex'], 'currently_here': info['currently_here'], 'player': info['player'],
            'movable': info['movable']}


@view_config(route_name='move_to', renderer='templates/game.pt', permission='play', request_method='POST')
def move_to(request):
    if 'position' in request.params:
        location = request.params['position']
        movement = send_player_to(location, request.authenticated_userid)
        request.session.flash(movement)

    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='attack_player', renderer='templates/game.pt', permission='play', request_method='POST')
def attack_player(request):
    if 'player_called' in request.params:
        attacker, defender = request.authenticated_userid, request.params['player_called']
        attack = player_attack(attacker=attacker, defender=defender)
        request.session.flash(attack)

    return HTTPFound(location=return_to_sender(request))


@view_config(route_name='team_info', renderer='templates/team.pt', permission='play')
def team_info(request):
    team_name = request.matchdict['team']
    info = get_team_info(team_name)
    if info:
        return {'team': info, 'player': get_player_info(request.authenticated_userid)}
    return HTTPFound(location=request.route_url('home'))


@view_config(route_name='profile', renderer='templates/profile.pt', permission='play')
def profile_page(request):
    player = get_player_info(request.authenticated_userid)
    if player:
        return {'player': player}
    return HTTPFound(location=return_to_sender(request))
