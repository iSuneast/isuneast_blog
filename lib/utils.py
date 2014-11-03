import os
import random
import hashlib
import string
import hmac
import webapp2
import jinja2
import datetime
from pytz.gae import pytz

class Handler(webapp2.RequestHandler):
    __template_dir = os.path.join(os.path.dirname(__file__), '../templates')
    __jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(__template_dir),
        autoescape = True)

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    @classmethod
    def render_str(cls, template, **params):
        t = cls.__jinja_env.get_template(template)
        return t.render(params)

    def valid_cookie_login(self):
        user_id = self.request.cookies.get('user_id')
        return Secure.valid_secure_value(user_id)

    def goto_login(self):
        self.redirect('/login')

    def render(self, template, **kw):
        if self.valid_cookie_login():
            username = self.get_login_name()
            if username:
                kw['login_name'] = username
        kw['system_time'] = Secure.get_format_system_time()

        self.write(self.render_str(template, **kw))

    def set_cookie(self, name, val):
        self.response.headers.add_header(
            'Set-Cookie',
            str('%s=%s; Path=/' % (name, val)))

    def set_secure_cookie(self, name, val):
        self.set_cookie(name, Secure.make_secure_value(val))

    def read_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val

    def get_login_name(self):
        return self.request.cookies.get('login_name')

    def read_secure_cookie(self, name):
        cookie_val = read_cookie(name)
        return cookie_val and Secure.check_secure_val(cookie_val)

    def login(self, user):
        self.set_cookie('login_name', user.username)
        self.set_secure_cookie('user_id', str(user.key().id()))
        self.redirect('/')

    def logout(self):
        self.set_cookie('user_id', '')
        self.redirect('/')

class Secure:
    # ''.join(random.choice(letters) for i in xrange(44))
    __secret = 'xdqiWAqpmAkUCxqaoIWeyLHKXqCxFLDeuHmbeqUNsUWz'

    @classmethod
    def make_secure_value(cls, val):
        return '%s|%s' % (val, hmac.new(cls.__secret, val).hexdigest())

    @classmethod
    def get_god_name(cls):
        return 'isuneast'

    @classmethod
    def get_system_time(cls):
        return datetime.datetime.now(pytz.timezone('Hongkong'))

    @classmethod
    def get_format_system_time(cls):
        return cls.format_time(cls.get_system_time())

    @classmethod
    def format_time(cls, time, hours_delta = 0):
        time = time + datetime.timedelta(hours=hours_delta)
        return time.strftime('%b %d, %Y %H:%M:%S HKT')

    @classmethod
    def valid_secure_value(cls, secure_value):
        if not secure_value:
            return False
        val = secure_value.split('|')[0]
        return secure_value == cls.make_secure_value(val)

    @classmethod
    def make_salt(cls, length = 5):
        return ''.join(random.choice(string.letters) for x in xrange(length))

    @classmethod
    def make_password_hash(cls, username, password, salt = None):
        if not salt:
            salt = cls.make_salt()
        password_hash = hashlib.sha256(username + password + salt).hexdigest()
        return '%s|%s' % (salt, password_hash)

    @classmethod
    def valid_password(cls, username, password, password_hash):
        salt = password_hash.split('|')[0]
        return password_hash == cls.make_password_hash(username, password, salt)

