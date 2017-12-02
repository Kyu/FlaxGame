import unittest
import random
import string

from pyramid import testing

"""
Keep getting warning, investigate:

flax/test.py::GameViews::test_team_info
  c:\ users\gp\desktop\dev\ firstsite\env\lib\site-packages\sqlalchemy\orm\scoping.py:106: SAWarning: At least one scoped session is already present.  configure() can not affect sessions that have already been created.
    warn('At least one scoped session is already present. '

-- Docs: http://doc.pytest.org/en/latest/warnings.html
=================== 10 passed, **8** warnings in 26.07 seconds ====================
..........
Process finished with exit code 0
"""


def _initTestingDB():
    import transaction
    from sqlalchemy import create_engine
    from .models import (
        DBSession,
        Player,
        User,
        Base
        )
    from .security import hash_password

    engine = create_engine('mysql+pymysql://new_game:#BattleFront1@localhost/users')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)

    with transaction.manager:
        new_test = User(username='test', email='test', password=hash_password('test'))
        test = Player(id=random.randint(4000, 90000), username='test', squad_type='Infantry', team='Red', location='2.2')
        testdummy = Player(id=random.randint(4000, 90000), username='testdummy', squad_type='Infantry', team='Yellow', location='2.2')
        testin99 = Player(id=random.randint(4000, 90000), username='testin99', squad_type='Infantry', team='Blue', location='9.9')
        DBSession.add_all([new_test, test, testdummy, testin99])
        transaction.commit()
    return DBSession


def remove_test_users():
    import transaction
    from sqlalchemy import or_
    from .models import User, Player, DBSession
    test_p = DBSession.query(User).filter_by(username='test').one()
    test_players = DBSession.query(Player).filter(or_(Player.username == 'test', Player.username == 'testdummy',
                                                      Player.username == 'testin99')).all()
    with transaction.manager:
        DBSession.delete(test_p)
        for i in test_players:
            DBSession.delete(i)
        transaction.commit()


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


# TODO Tests failing because not being allowed to log in
class GameViews(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = _initTestingDB()

    def setUp(self):
        from pyramid.paster import get_app
        app = get_app('../development.ini')
        from webtest import TestApp
        self.testapp = TestApp(app)
        login = self.testapp.post('/login', params={'username': 'test', 'password': 'test', 'login': ''}, status=302)
        self.assertIn("Logged in successfully", login.text)

    @classmethod
    def tearDownClass(cls):
        remove_test_users()
        cls.session.remove()

    def test_game_page(self):
        game_page = self.testapp.get('/game', status=200)
        self.assertIn('Logout', game_page.text)
        self.assertIn('Actions:', game_page.text)
    '''
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

        from .models import Player
        old_location = self.session.query(Player).filter_by(username='test').one().location

        good_movement = self.move_to('3.2')
        self.assertIn("Successfully moved from 2.2 to 3.2", good_movement.text)
        new_location = self.session.query(Player).filter_by(username='test').one().location

        self.assertEqual(new_location, '3.2')
        self.assertNotEqual(new_location, old_location)

        move_back = self.move_to('2.2')
        self.assertIn("Successfully moved from 3.2 to 2.2", move_back.text)

        back = self.session.query(Player).filter_by(username='test').one().location
        self.assertEqual(back, '2.2')

    def attack_player(self, player):
        self.testapp.post('/attack', params={'player_called': player})
        home = self.testapp.get('/game')
        return home

    def test_attacking(self):
        from .models import Player
        random_user = ''.join(random.choice(string.ascii_lowercase) for i in range(50))
        nonexistent_attack = self.attack_player(random_user)
        self.assertIn("Player does not exist", nonexistent_attack.text)

        too_far_attack = self.attack_player('testin99')
        self.assertIn("You are not in the same location as this player!", too_far_attack.text)

        current_troops = self.session.query(Player).filter_by(username='test').one().troops
        good_attack = self.attack_player('testdummy')
        self.assertIn('lost', good_attack.text)
        new_troops = self.session.query(Player).filter_by(username='test').one().troops

        self.assertLess(new_troops, current_troops)

    def test_team_info(self):
        bad_team = self.testapp.get('/team/winners')
        self.assertIn('Team not found', bad_team.text)

        other_team = self.testapp.get('/team/Blue')
        self.assertIn('Members:', other_team.text)

        my_team = self.testapp.get('/team/Red')
        self.assertIn('Name:', my_team.text)

    def test_profile_pate(self):
        info = self.testapp.get('/profile')
        self.assertIn('Player: test', info.text)

    def test_setting_change(self):
        from .models import User

        old_email = self.session.query(User).filter_by(username='test').one().email
        change = self.testapp.post('/settings/modify', params={'password': 'test', 'new_value': 'test@test.test', 'setting': 'email'})
        self.assertIn('email changed successfully', change.text)
        new_email = self.session.query(User).filter_by(username='test').one().email

        self.assertEqual(new_email, 'test@test.test')
        self.assertNotEqual(old_email, new_email)

    def delete_message(self, msg):
        import transaction
        from .models import Radio
        msg = self.session.query(Radio).filter_by(message=msg).one()
        with transaction.manager:
            self.session.delete(msg)
            transaction.commit()

    def test_send_message(self):
        random_text = ''.join(random.choice(string.ascii_lowercase) for i in range(50))
        self.testapp.post('/message', params={'message': random_text})
        home = self.testapp.get('/game')
        self.assertIn(random_text, home.text)
    '''
    def test_logout(self):
        logout = self.testapp.post('/logout')
        self.assertIn('{"logged_out":true}', logout.text)