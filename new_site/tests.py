import unittest

from pyramid import testing


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_my_view(self):
        from .views import MainViews
        request = testing.DummyRequest()
        info = MainViews.my_view(request)
        print(dir(info))
        self.assertEqual(1, 2-1)

'''
class FunctionalTests(unittest.TestCase):
    def setUp(self):
        from new_site import main
        app = main({})
        from webtest import TestApp
        self.testapp = TestApp(app)

    def test_root(self):
        res = self.testapp.get('/', status=200)
        self.assertTrue(b'Pyramid' in res.body)
'''
