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
    from sqlalchemy import engine_from_config
    from pyramid.paster import get_appsettings
    from .models import (
        DBSession,
        Player,
        User,
        Base
        )
    DBSession.remove()
    from .security import hash_string
    settings = get_appsettings('development.ini')
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    with transaction.manager:
        new_test = User(username='test', email='test', password=hash_string('test'))
        DBSession.add(new_test)
        transaction.commit()
        test = Player(id=new_test.id, username='test', squad_type='Infantry', team='Red', location='2.2')
        testdummy = Player(id=random.randint(4000, 90000), username='testdummy', squad_type='Infantry', team='Yellow', location='2.2')
        testin99 = Player(id=random.randint(4000, 90000), username='testin99', squad_type='Infantry', team='Blue', location='9.9')
        DBSession.add_all([test, testdummy, testin99])
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


class StaticViews(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_home(self):
        from .views import home
        request = testing.DummyRequest()
        response = home(request)
        self.assertIsNone(response['name'])


class GameViews(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from .models import Player, User
        cls.session = _initTestingDB()
        test_player = cls.session.query(Player).filter_by(username='test').one()
        test_user = cls.session.query(User).filter_by(username='test').one()
        assert test_player
        assert test_user
        assert test_player.id == test_user.id
        assert test_player.username == test_user.username
        # This is just PTSD don't worry about it

    def setUp(self):
        from pyramid.paster import get_app
        app = get_app('development.ini')
        from webtest import TestApp
        self.testapp = TestApp(app)

        data = {'username': 'test', 'password': 'test', 'login': ''}
        login = self.testapp.post('/login', params=data)
        json_resp = login.json
        self.assertTrue(json_resp['success'])

    def tearDown(self):
        logout = self.testapp.post('/logout')
        logout_json = logout.json
        self.assertTrue(logout_json['success'])
        self.assertFalse(self.testapp.cookiejar)

    @classmethod
    def tearDownClass(cls):
        remove_test_users()
        cls.session.remove()

    def test_game_page(self):
        game_page = self.testapp.get('/game')
        self.assertIn('Actions:', game_page.text)
        # self.assertIn('Logout', game_page.text)

    def text_hex_view(self):
        hex_page = self.testapp.get('/game/2.2', status=200)
        self.assertIn("Currently here", hex_page.text)
        self.assertIn("You are here!", hex_page.text)

    def move_to(self, position):
        movement = self.testapp.post('/game/action/go_to', params={'position': position})
        return movement

    def test_moving(self):
        bad_move = self.move_to('2.2')
        self.assertIn('The location you are trying to move to is the same location you are currently in',
                      bad_move.json['result'])

        non_existent_move = self.move_to('11.10')
        self.assertIn('This location does not exist', non_existent_move.json['result'])

        too_far_movement = self.move_to('9.9')
        self.assertIn('This location is not next to your current location', too_far_movement.json['result'])

        from .models import Player
        old_location = self.session.query(Player).filter_by(username='test').one().location

        good_movement = self.move_to('3.2')
        self.assertIn("Successfully moved from 2.2 to 3.2", good_movement.json['result'])
        new_location = self.session.query(Player).filter_by(username='test').one().location

        self.assertEqual(new_location, '3.2')
        self.assertNotEqual(new_location, old_location)

        move_back = self.move_to('2.2')
        self.assertIn("Successfully moved from 3.2 to 2.2", move_back.json['result'])

        back = self.session.query(Player).filter_by(username='test').one().location
        self.assertEqual(back, '2.2')

    def attack_player(self, player):
        attack = self.testapp.post('/game/action/attack', params={'player_called': player})
        return attack

    def test_attacking(self):
        from .models import Player
        random_user = ''.join(random.choice(string.ascii_lowercase) for i in range(50))
        nonexistent_attack = self.attack_player(random_user)
        self.assertIn("Player does not exist", nonexistent_attack.json['result'])

        too_far_attack = self.attack_player('testin99')
        self.assertIn("You are not in the same location as this player!", too_far_attack.json['result'])

        current_troops = self.session.query(Player).filter_by(username='test').one().troops
        good_attack = self.attack_player('testdummy')
        self.assertIn('lost', good_attack.json['result'])  # How did I know he was gonna lose?

        new_troops = self.session.query(Player).filter_by(username='test').one().troops

        self.assertLess(new_troops, current_troops)

    def test_team_info(self):
        bad_team = self.testapp.get('/team/winners')
        self.assertIn('Team not found', bad_team.text)

        other_team = self.testapp.get('/team/Blue')
        self.assertIn('Members:', other_team.text)

        my_team = self.testapp.get('/team/Red')
        self.assertIn('Name:', my_team.text)

    def test_profile_pate(self):  # add a /info/player
        info = self.testapp.get('/profile')
        self.assertIn('Player: test', info.text)

    # TODO Doesn't work
    ''' 
    def test_setting_change(self):
        from .models import User

        old_email = self.session.query(User).filter_by(username='test').one().email
        change = self.testapp.post('/settings/modify', params={'password': 'test', 'new_value': 'test@test.test', 'setting': 'email'})
        self.assertIn('email changed successfully', change.text)
        new_email = self.session.query(User).filter_by(username='test').one().email

        self.assertEqual(new_email, 'test@test.test')
        self.assertNotEqual(old_email, new_email)
    '''

    def delete_message(self, msg):
        import transaction
        from .models import Radio
        msg = self.session.query(Radio).filter_by(message=msg).one()
        with transaction.manager:
            self.session.delete(msg)
            transaction.commit()

    def test_send_message(self):
        random_text = ''.join(random.choice(string.ascii_lowercase) for i in range(50))
        send_msg = self.testapp.post('/game/action/message', params={'message': random_text})
        self.assertTrue(send_msg.json['success'])
        self.assertEqual(send_msg.json['message']['content'], random_text)

        home = self.testapp.get('/game')
        self.assertIn(random_text, home.text)

        self.delete_message(random_text)
    

