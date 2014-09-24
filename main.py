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
import matplotlib.pyplot as plt
import pprint
import datetime
from google.appengine.ext import db
plt.switch_backend('Agg')


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

    def goto_login(self):
        self.redirect('/login')

    def render(self, template, **kw):
        if self.valid_cookie_login():
            username = self.get_login_name()
            if username:
                kw['login_name'] = username
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
        touch_db = self.request.get('touch_db')
        if touch_db != '':
            if not self.valid_cookie_login() or self.get_login_name() != Secure.get_god_name():
                self.goto_login()
            else:
                Activity().flush(touch_db == 'reset')
                self.redirect('/')
                return 
        self.render('main.html', activity=Activity().content())


class Diary(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)

    @classmethod
    def by_subject(cls, subject):
        return cls.all().filter('subject = ', subject).get()

    @classmethod
    def clear(cls):
        for diary in cls.all():
            diary.delete()

    @classmethod
    def insert_diary(cls, subject, content):
        diary = cls.by_subject(subject)
        if diary:
            if content != diary.content:
                diary.content = content
                diary.put()
        else:
            diary = Diary(subject = subject, content = content)
            diary.put()


class Activity(Handler):
    def content(self):
        cache = Diary.by_subject('cache')
        if cache:
            return eval(cache.content)
        else:
            return self.flush()

    def flush(self, reset = False):
        if reset:
            Diary.clear()
        url = 'http://i.cs.hku.hk/~wbtang/have_fun.txt'
        activity = ['run', 'pull up', 'horizontal bar', 'sit up']

        Diary.insert_diary(subject = 'activity', content = repr(activity))
        Diary.insert_diary(subject = 'since', content = '20140911')

        self.parse_raw_data(url, activity)
        date, activity, labels = self.parse_database(activity)
        x, y = self.decode_data(date, activity, labels, since='20140911')
        img_b64 = self.draw(x, y, labels)

        cache = self.render_str('activity.html', image_activity=img_b64, 
            date = date, activity = activity, labels = labels)
        Diary.insert_diary(subject = 'cache', content = repr(cache))

        return cache

    @classmethod
    def decode_data(cls, date, activity, labels, since):
        total = cls.date_dif(date[-1], since)
        x = [i for i in range(total+1)]
        y = [[0 for j in range(len(labels))] for i in range(total+1)]
        for i in range(len(date)):
            pos = cls.date_dif(date[i], since) 
            y[pos] = [sum(t) for t in activity[i]]
        return x, y

    @classmethod
    def date_dif(cls, date, since):
        d0 = datetime.date(int(date[:4]), int(date[4:6]), int(date[6:8]))
        d1 = datetime.date(int(since[:4]), int(since[4:6]), int(since[6:8]))
        return (d0-d1).days

    @classmethod
    def parse_database(cls, activity):
        data = {}
        for diary in Diary.all():
            if diary.subject.isdigit():
                data[diary.subject] = eval(diary.content)

        x = sorted(data.iterkeys())
        y = []
        labels = activity
        for key in x:
            day = data[key]
            format_day = []
            for act in activity:
                if act in day:
                    format_day.append(day[act])
                else:
                    format_day.append([0])
            y.append(format_day)

        return x, y, activity

    @classmethod
    def parse_raw_data(cls, url, activity):
        u = urllib2.urlopen(url)
        if u is None:
            print '---------------- Can not open "%s"' % url
            return

        data = {}
        date = ''
        for line in u.readlines():
            tokens = filter(bool, line.replace('\r', '').replace('\n', '').split(' '))
            if len(tokens) == 0:
                continue

            if tokens[0] == '#':
                if data != {}:
                    Diary.insert_diary(subject = date, content = repr(data))
                date = tokens[1]
                data = {}
            elif tokens[0] == '>':
                if date == '':
                    continue
                act = ' '.join(tokens[1].split('_')).lower()
                if act not in activity:
                    print('UNKNOWN activity: "%s"' % act)
                else:
                    data[act] = [int(num) for num in tokens[2:]]
            else:
                pass
        if data != {}:
            Diary.insert_diary(subject = date, content = repr(data))


    @classmethod
    def draw(cls, x, y, labels):
        for id in range(len(labels)):
            ax = plt.subplot(len(labels), 1, id+1)
            ax.plot(x, [y[i][id] for i in range(len(y))], 'ro-', markersize=12)
            plt.xticks([])
            plt.title(labels[id])
        plt.tight_layout()

        sio = StringIO.StringIO()
        plt.savefig(sio, format="png")
        img_b64 = sio.getvalue().encode("base64").strip()
        plt.clf()
        sio.close()

        return img_b64


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/login', LogInPage),
    ('/signup', SignUpPage),
    ('/logout', LogOutPage),
    ], debug = True)
