from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory

from pyramid_mailer import mailer_factory_from_settings

from sqlalchemy import engine_from_config

from .models import DBSession, Base
from .security import groupfinder


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    # Database setup
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    # Session, config
    my_session_factory = SignedCookieSessionFactory('itsaseekreet')
    config = Configurator(settings=settings, session_factory=my_session_factory,
                          root_factory='.models.Root')
    config.include('pyramid_chameleon')
    config.registry['mailer'] = mailer_factory_from_settings(settings)

    # Security policies
    authn_policy = AuthTktAuthenticationPolicy(
        settings['flax.secret'], callback=groupfinder,
        hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    # Views
    # Home/Main views
    config.add_static_view('static', 'static', cache_max_age=int(settings['cache_max_age']))
    config.add_route('home', '/')
    config.add_route('game', '/game')
    config.add_route('test_view', '/test')

    # Game/Action views
    config.add_route('hex_view', '/game/{loc_name}')
    config.add_route('get_ammo', '/game/action/ammo')
    config.add_route('recruit', '/game/action/recruit')
    config.add_route('upgrade_industry', '/game/action/industry')
    config.add_route('upgrade_infrastructure', '/game/action/infrastructure')
    config.add_route('attack_player', 'game/action/attack')
    config.add_route('movement', '/game/action/go_to')
    config.add_route('level_up', '/game/action/level_up')
    config.add_route('send_message', '/game/action/message')
    config.add_route('dig_in', '/game/action/dig_in')

    # Game info views
    config.add_route('my_info', '/game/info/my_info')
    config.add_route('current_hex_info', '/game/info/current_loc_info')
    config.add_route('map_info', '/game/info/map')

    # Personal/Information views
    config.add_route('team_info', '/team/{team}')
    config.add_route('profile', '/profile')
    config.add_route('levelup', '/settings/levelup')
    config.add_route('change_setting', '/settings/modify')

    # Authentication views
    config.add_route('register', '/register')
    config.add_route('login', '/login')
    config.add_route('ip_login', 'oneclick')
    config.add_route('logout', '/logout')
    config.add_route('verify', '/verify')
    config.add_route('recover_password', '/recover')

    # Admin views
    config.add_route('admin', '/admin')
    config.add_route('ban_player', '/ban')
    config.add_route('unban_player', '/unban')
    config.add_route('player_info', '/pinfo')
    config.add_route('broadcast', '/broadcast')
    config.add_route('hide_broadcast', '/hide_broadcast')

    config.scan('.views')
    return config.make_wsgi_app()
