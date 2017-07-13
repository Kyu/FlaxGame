import unittest
import random
import string


import transaction
from pyramid import testing


def _initTestingDB():
    from sqlalchemy import create_engine
    from .models import (
        DBSession,
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

    def move_to(self, position):
        self.testapp.post('/goto', params={'position': position})
        home = self.testapp.get('/game')
        return home

    def test_moving(self):
        bad_move = self.move_to('2.2')
        self.assertIn('The location you are trying to move to is the same location you are currently in', bad_move.text)

        non_existent_move = self.move_to('11.10')
        self.assertIn('This location does not exist', non_existent_move.text)

        too_far_movement = self.move_to('9.9')
        self.assertIn('This location is not next to your current location', too_far_movement.text)

        good_movement = self.move_to('3.2')
        self.assertIn("Successfully moved from 2.2 to 3.2", good_movement.text)

        move_back = self.move_to('2.2')
        self.assertIn("Successfully moved from 3.2 to 2.2", move_back.text)

    def attack_player(self, player):
        self.testapp.post('/attack', params={'player_called': player})
        home = self.testapp.get('/game')
        return home

    def test_attacking(self):
        random_user = ''.join(random.choice(string.ascii_lowercase) for i in range(50))
        nonexistent_attack = self.attack_player(random_user)
        self.assertIn("Player does not exist", nonexistent_attack.text)

        too_far_attack = self.attack_player('testin99')
        self.assertIn("You are not in the same location as this player!", too_far_attack.text)

        good_attack = self.attack_player('testdummy')
        self.assertIn('You cannot attack your teammate', good_attack.text)

        # TODO attack person who respawns in same location over and over
    # TODO attacking, team info, profile page

    def test_logout(self):
        logout = self.testapp.post('/logout')
        self.assertIn('Logged out successfully', logout.text)
