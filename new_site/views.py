from pyramid.httpexceptions import HTTPFound

from pyramid.security import (
    remember, 
    forget
)

from pyramid.view import (
    view_config,
    view_defaults,
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
# TODO maybe change all views classes to functions?


def return_to_sender(request):
    if request.referer == request.url:
        return '/'
    return request.referer


@view_defaults(route_name='main', renderer='templates/default.pt')
class MainViews(object):
    # Maybe use view funcs instead?
    
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid
        self.view_name = 'HomePageViews'

    @view_config(route_name='home')
    @forbidden_view_config(renderer='templates/default.pt')
    def home(self):
        if self.logged_in:
            return HTTPFound('/game')

        resp = {'page_title': 'GAMENAMEHERE - DESCRIPTION', 'name': self.logged_in}
        return resp

    # /login shit
    @view_config(route_name='hello', renderer='templates/mytemplate.pt')
    def my_view(request):
        return {'project': 'new_site'}

    @view_config(request_method='POST', route_name='register')
    def register(self):
        request = self.request
        # referrer = request.url
        # came_from = request.params.get('came_from', referrer)

        if self.logged_in:
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

    @view_config(request_method='POST', route_name='login')
    def login(self):
        request = self.request
        message = ''
        password = ''
        home = request.route_url('home')
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
                    return HTTPFound(location=home, headers=headers)
                else:
                    message = verified['status']

            request.session.flash(message)
        return HTTPFound(location='/')
    
    @view_config(route_name='logout')
    def logout(self):
        request = self.request
        headers = forget(request)
        url = request.route_url('home')
        return HTTPFound(location=url, headers=headers)
    
    '''
    @view_config(route_name='home', renderer='templates/home.pt')
    def home(self):
        return {'page_title': 'GAMENAMEHERE - DESCRIPTION'}
    '''


@view_defaults(route_name='game', renderer='templates/game.pt')
class GameViews:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid

    @view_config(route_name='game', renderer='templates/game.pt')
    def game(self):
        info = get_all_game_info_for(self.logged_in)
        return {'page_title': 'GAMENAMEHERE - DESCRIPTION', 'name': self.logged_in, 'hexes': info['hexes'],
                'player': info['player'], 'current_hex': ''}

    @view_config(route_name='hex_view', renderer='templates/game.pt')
    def hex_view(self):
        hex_name = self.request.matchdict['name']
        info = get_all_game_info_for(self.logged_in, hex_name)

        return {'page_title': 'GAMENAMEHERE - DESCRIPTION', 'name': self.logged_in, 'hexes': info['hexes'],
                'current_hex': info['current_hex'], 'currently_here': info['currently_here'], 'player': info['player'],
                'movable': info['movable']}

    @view_config(route_name='move_to', renderer='templates/game.pt', request_method='POST')
    def move_to(self):
        if 'position' in self.request.params:
            location = self.request.params['position']
            movement = send_player_to(location, self.logged_in)
            self.request.session.flash(movement)

        return HTTPFound(location=return_to_sender(self.request))

    @view_config(route_name='attack_player', renderer='templates/game.pt', request_method='POST')
    def attack(self):
        if 'player_called' in self.request.params:
            attacker, defender = self.logged_in, self.request.params['player_called']
            attack = player_attack(attacker=attacker, defender=defender)
            self.request.session.flash(attack)

        return HTTPFound(location=return_to_sender(self.request))

    @view_config(route_name='team_info', renderer='templates/team.pt')
    def team_info(self):
        team_name = self.request.matchdict['team']
        team_info = get_team_info(team_name)
        if team_info:
            return {'team': team_info, 'player': get_player_info(self.logged_in)}
        return HTTPFound(location=self.request.route_url('home'))





