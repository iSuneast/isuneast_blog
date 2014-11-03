#encoding:utf-8
import re
from google.appengine.ext import db
from lib.utils import Handler, Secure

class User(db.Model):
    username = db.StringProperty(required = True)
    password_hash = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

    @classmethod
    def by_name(cls, username):
        username = username.lower()
        return User.all().filter('username = ', username).get()

    @classmethod
    def register(cls, username, password):
        username = username.lower()
        password_hash = Secure.make_password_hash(username, password)
        user = User(username = username, password_hash = password_hash)
        user.put()
        return user

    @classmethod
    def login(cls, username, password):
        user = cls.by_name(username)
        if not user:
            print 'user not found'
        else:
            print 'user found: %s ' % user.username
        if user and Secure.valid_password(username, password, user.password_hash):
            return user


class LogInPage(Handler):
    def get(self):
        username = self.request.cookies.get('username')
        if username is None:
            username = ''
        self.render('login.html', username = username)

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        user = User.by_name(username)
        error = ''
        if not user:
            error = 'Invalid Username'
        elif not Secure.valid_password(username, password, user.password_hash):
            error = 'Invalid Password'

        if error == '':
            self.login(user)
        else:
            self.render('login.html', username = username, error = error)


class LogOutPage(Handler):
    def get(self):
        self.logout()


class SignUpPage(Handler):
    __USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    __PASS_RE = re.compile(r"^.{3,20}$")

    @staticmethod
    def valid_username(username):
        return username and SignUpPage.__USER_RE.match(username)

    @staticmethod
    def valid_password(password):
        return password and SignUpPage.__PASS_RE.match(password)

    def get(self):
        self.render('signup.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')

        error = ''
        if not SignUpPage.valid_username(username):
            error = 'Invalid Username'
        elif username.lower() != 'isuneast':
            error = 'The registration is closed'
        elif not SignUpPage.valid_password(password):
            error = 'Invalid Password'
        elif password != verify:
            error = 'Password does NOT match'
        elif User.by_name(username) is not None:
            error = 'Username already exisit. ToT'

        if error != '':
            self.render('signup.html', username = username, error = error)
        else:
            self.signup(username, password)

    def signup(self, username, password):
        user = User.register(username, password)
        self.login(user)
