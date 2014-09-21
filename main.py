import os
import re
import random
import hashlib
import string
import hmac
import urllib2
import json
import webapp2
import jinja2
import StringIO
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from google.appengine.ext import db


class Handler(webapp2.RequestHandler):
    __template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    __jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(__template_dir),
        autoescape = True)

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = self.__jinja_env.get_template(template)
        return t.render(params)

    def valid_cookie_login(self):
        user_id = self.request.cookies.get('user_id')
        return Secure.valid_secure_value(user_id)

    def render(self, template, **kw):
        if self.valid_cookie_login():
            username = self.request.cookies.get('login_name')
            if username:
                kw['login_name'] = username
        self.write(self.render_str(template, **kw))

    def set_cookie(self, name, val):
        self.response.headers.add_header(
            'Set-Cookie',
            str('%s=%s; Path=/' % (name, val)))

    def set_secure_cookie(self, name, val):
        self.set_cookie(name, Secure.make_secure_value(val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
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


class User(db.Model):
    username = db.StringProperty(required = True)
    password_hash = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

    @classmethod
    def by_name(cls, username):
        return User.all().filter('username = ', username).get()

    @classmethod
    def register(cls, username, password):
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


class MainPage(Handler):
    def get(self):
#        self.render('main.html')
        plt.plot(np.random.random((20)),"r-")
        sio = cStringIO.StringIO()
        plt.savefig(sio, format="png")
        self.response.headers['Content-Type'] = 'image/png'

        self.response.out.write(sio.getvalue())

class Diary(db.Model):
    created = db.StringProperty(required = True)
    content = db.StringProperty(required = True)

    @classmethod
    def by_created(cls, created):
        return Diary.all().filter('created = ', created).get()

    @classmethod
    def insert_diary(cls, created, content):
        diary = cls.by_created(created)
        if not diary:
            Diary(created=created, content=content).put()
            return True
        return False


class NewPostPage(Handler):
    def get(self):
        if not self.valid_cookie_login():
            self.redirect('/login')
            return 
        num_new_entry = self.parse('http://i.cs.hku.hk/~wbtang/have_fun.txt')

        plt.plot(np.random.random((20)))
        sio = StringIO.StringIO()
        plt.savefig(sio, format="png")
        img_b64 = sio.getvalue().encode("base64").strip()
        plt.clf()
        sio.close()
        self.response.write("""<html><body>""")
        self.response.write("<img src='data:image/png;base64,%s'/>" % img_b64)
        self.response.write("""</body> </html>""")

    def parse(self, url):
        u = urllib2.urlopen(url)
        created = ''
        data = {}
        num_new_entry = 0
        for line in u.readlines():
            tokens = filter(bool, line.replace('\r', '').replace('\n', '').split(' '))
            if len(tokens) == 0:
                continue

            if tokens[0] == '#':
                created = tokens[1]
            elif tokens[0] == '>':
                data[tokens[1].upper()] = tokens[2:]
            elif tokens[0] == '<':
                content = json.dumps(data)
                if not Diary.insert_diary(created, content):
                    break
                else:
                    num_new_entry += 1
                data.clear()
            elif created != '':
                log = ' '.join(tokens)
                key = 'log'
                if key in data:
                    data[key].append(log)
                else:
                    data[key] = [log]

        return num_new_entry


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/newpost', NewPostPage),
    ('/login', LogInPage),
    ('/signup', SignUpPage),
    ('/logout', LogOutPage),
    ], debug = True)
