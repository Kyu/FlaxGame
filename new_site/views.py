from datetime import datetime

from pyramid.httpexceptions import HTTPFound

from pyramid.security import (
    remember, 
    forget
)

from pyramid.view import (
    view_config,
    view_defaults
)

from .models import (
    DBSession,
    User
)

from .security import (
    check_password,
    hash_password
)


@view_defaults(route_name='hello', renderer='templates/home.pt')
class MainViews(object):
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid
        self.view_name = 'HomePageViews'

    @view_config(route_name='home')
    def home(self):
        return {'name': self.request.authenticated_userid, 'message': ''}

    @view_config(route_name='register', renderer='templates/register.pt')
    def register(self):
        request = self.request
        referrer = request.url
        came_from = request.params.get('came_from', referrer)

        if self.logged_in:
            return HTTPFound(location=came_from)
        message = ''
        login = ''
        password = ''
        email = ''
        if 'form.submitted' in request.params:
            login = request.params['login'] # change to username
            password = request.params['password']
            email = request.params['email']
            if email and password and email:
                new_user = User(username=login, email=email, hash_string=hash_password(password),
                                created_at=datetime.utcnow())
                DBSession.add(new_user)
                return HTTPFound(location='/')
            
            message = 'Failed to register'
        # DBSession.add(User(username=, email=, hash_string=, created_at=))
        return {'name': 'Register', 'message': message}


    @view_config(request_method='POST', route_name='login')
    def login(self):
        request = self.request
        login_url = self.request.route_url('login')
        referrer = request.url
        if referrer == login_url:
            referrer = '/' # don't use login form itself as came_from
        came_from = request.params.get('came_from', referrer)
        message = ''
        login = ''
        password = ''
        if 'form.submitted' in request.params:
            login = request.params['login'] # change to username
            password = request.params['password']
            try:
                expected_password = DBSession.query(User).filter_by(username=login).one().hash_string
                verified = check_password(password, expected_password)
                if verified:
                    headers = remember(request, login)
                    return HTTPFound(location='/', headers=headers, comment='wew')
            except Exception as e: # sqlalchemy.orm.exc.NoResultFound :: when username not found
                print(type(e).__name__ + ': ' + str(e))
                pass
            
            message = 'Failed Login'
        return dict(
            name='',
            message=message,
            url=request.application_url + '/login',
            came_from=came_from,
            login=login,
            password=password,
        )
        return HTTPFound(location=came_from, comment=message)
    
    @view_config(route_name='hello', renderer='templates/mytemplate.pt')
    def my_view(request):
        return {'project': 'new_site'}

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