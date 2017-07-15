from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory

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

    # Security policies
    authn_policy = AuthTktAuthenticationPolicy(
        settings['new_site.secret'], callback=groupfinder,
        hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    # Views
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('game', '/game')

    config.add_route('hex_view', '/game/{name}')
    config.add_route('get_ammo', '/game/action/ammo')
    config.add_route('recruit', '/game/action/recruit')
    config.add_route('upgrade_industry', '/game/action/upgrade')
    config.add_route('upgrade_infrastructure', '/game/action/infrastructure')

    config.add_route('team_info', '/team/{team}')
    config.add_route('profile', '/profile')
    config.add_route('levelup', '/settings/levelup')
    config.add_route('change_setting', '/settings/modify')

    config.add_route('attack_player', '/attack')
    config.add_route('move_to', 'goto')
    config.add_route('level_up', '/levelup')

    config.add_route('register', '/register')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.scan()
    return config.make_wsgi_app()
