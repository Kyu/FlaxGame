import unittest

import transaction
from pyramid import testing

# TODO You should really work on these

def _initTestingDB():
    from sqlalchemy import create_engine
    from .models import (
        DBSession,
        User,
        Player,
        Hex,
        Team,
        Base
        )
    engine = create_engine('mysql+pymysql://new_game:#BattleFront1@localhost/users')
    Base.metadata.create_all(engine)
    DBSession.configure(bind=engine)
    return DBSession


class HomeViews(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_home(self):
        from .views import home
        request = testing.DummyRequest()
        response = home(request)
        self.assertIsNone(response['name'])

    def test_bad_request_method(self):
        from .views import login
        request = testing.DummyRequest()
        response = login(request)
        self.assertEqual(response.status_code, 302)


class GameViews(unittest.TestCase):
    def setUp(self):
        from pyramid.paster import get_app
        app = get_app('../development.ini')
        from webtest import TestApp
        self.testapp = TestApp(app)
        login = self.testapp.post('/login', params={'username': 'test', 'password': 'test', 'login': ''}, status=302)
        self.assertIn('Logged in successfully', login.text)

    def tearDown(self):
        from .models import DBSession
        DBSession.remove()

    def test_game_page(self):
        game_page = self.testapp.get('/game', status=200)
        self.assertIn('Logout', game_page.text)
        self.assertIn('Actions:', game_page.text)

    def text_hex_view(self):
        hex_page = self.testapp.get('/game/2.2', status=200)
        self.assertIn("Currently here", hex_page.text)
        self.assertIn("You are here!", hex_page.text)

    # TODO Moving, attacking, team info, profile page

    def test_logout(self):
        logout = self.testapp.post('/logout')
        self.assertIn('Logged out successfully', logout.text)


