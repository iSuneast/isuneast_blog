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
from pytz.gae import pytz
from google.appengine.ext import db
from lib.utils import Handler, Secure

plt.switch_backend('Agg')

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


class SportDiary(db.Model):
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
            diary = SportDiary(subject = subject, content = content)
            diary.put()


class Activity(Handler):
    def content(self):
        cache = SportDiary.by_subject('cache')
        if cache:
            return eval(cache.content)
        else:
            return self.flush()

    def flush(self, reset = False):
        if reset:
            SportDiary.clear()
        url = 'http://i.cs.hku.hk/~wbtang/have_fun.txt'
        activity = ['run', 'pull up', 'horizontal bar', 'sit up']

        SportDiary.insert_diary(subject = 'activity', content = repr(activity))
        SportDiary.insert_diary(subject = 'since', content = '20140911')

        self.parse_raw_data(url, activity)
        date, activity, labels = self.parse_database(activity)
        x, y = self.decode_data(date, activity, labels, since='20140911')
        img_b64 = self.draw(x, y, labels)

        cache = self.render_str('activity.html', image_activity=img_b64, 
            date = date, activity = activity, labels = labels,
            last_updated = Secure.get_format_system_time())
        SportDiary.insert_diary(subject = 'cache', content = repr(cache))

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
        for diary in SportDiary.all():
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
                    SportDiary.insert_diary(subject = date, content = repr(data))
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
            SportDiary.insert_diary(subject = date, content = repr(data))


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


class Diary(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(required = True)

    def get_subject(self):
        return self.subject

    def get_content(self, raw=False):
        if raw:
            return eval(self.content)
        return eval(self.content).replace('\n', '<br>')

    def get_created(self):
        return Secure.format_time(self.created, 8)

    def get_id(self):
        return self.key().id()

    def as_dict(self):
        return {
            'subject': self.subject,
            'content': eval(self.content),
            'created': self.created.strftime('%c'),
            }

    @classmethod
    def update(cls, subject, content, id):
        diary = None
        if id:
            diary = Diary.get_by_id(id)
        if diary:
            diary.subject = subject
            diary.content = content
        else:
            diary = Diary(subject=subject, content=content, 
                created = Secure.get_system_time())
        
        diary.put()


class DiaryPage(Handler):
    def get(self):
        diaries = Diary.all().order('-created')

        q = self.request.get('q')
        if q and q == 'json':
            self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
            self.write(json.dumps([diary.as_dict() for diary in diaries],
             ensure_ascii=False))
        else:
            self.render('diaries.html', diaries = diaries)


class NewDiaryPage(Handler):
    def get(self):
        if not self.valid_cookie_login() or self.get_login_name() != Secure.get_god_name():
            self.goto_login()
            return

        diary_id = self.request.get('id')
        if diary_id:
            diary = Diary.get_by_id(long(diary_id))
            if diary:
                op = self.request.get('op')
                if op == 'del':
                    diary.delete()
                    self.redirect('/diary')
                else:
                    self.render('newdiary.html', subject=diary.subject, 
                        content=diary.get_content(raw=True))
                    return 
        self.render('newdiary.html')

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')
        error = ''
        if not subject:
            error += 'subject is empty!!!'
        elif not content:
            error += 'content is empty!!!'
        if error != '':
            self.render('newdiary.html', subject=subject, content=content,
                 error=error)
            return

        diary_id = self.request.get('id')
        if not diary_id:
            diary_id = 0
        else:
            diary_id = long(diary_id)
        Diary.update(subject=subject, content=repr(content), id=diary_id)

        self.redirect('/diary')


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/diary', DiaryPage),
    ('/newdiary', NewDiaryPage),
    ('/login', LogInPage),
    ('/signup', SignUpPage),
    ('/logout', LogOutPage),
    ], debug = True)
