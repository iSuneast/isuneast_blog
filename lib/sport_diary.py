#encoding:utf-8
import urllib2
import StringIO
import matplotlib.pyplot as plt
import datetime
from google.appengine.ext import db
from lib.utils import Handler, Secure
from lib.user import User, LogInPage, LogOutPage, SignUpPage

plt.switch_backend('Agg')


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
        event_en = ['run', 'pull up', 'push up'] # , 'sit up', 'horizontal bar'
        event_cn = [u'跑步', u'引体向上', u'俯卧撑']

        self.parse_raw_data(url, event_en)
        date, activity = self.parse_database(event_en)
        x, y = self.decode_data(date, activity, since='20140911')
        img_b64 = self.draw(x, y, labels=event_en)

        cache = self.render_str('activity.html', image_activity=img_b64, 
            date = date, activity = activity, labels = event_cn,
            last_updated = Secure.get_format_system_time())
        SportDiary.insert_diary(subject = 'cache', content = repr(cache))

        return cache

    @classmethod
    def decode_data(cls, date, activity, since):
        total = cls.date_dif(date[-1], since)
        x = [i for i in range(total+1)]
        y = [[0 for j in range(len(activity))] for i in range(total+1)]
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
    def parse_database(cls, event):
        data = {}
        for diary in SportDiary.all():
            if diary.subject.isdigit():
                data[diary.subject] = eval(diary.content)

        x = sorted(data.iterkeys())
        y = []
        for key in x:
            day = data[key]
            format_day = []
            for e in event:
                if e in day:
                    format_day.append(day[e])
                else:
                    format_day.append([0])
            y.append(format_day)

        return x, y

    @classmethod
    def parse_raw_data(cls, url, event):
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
                e = ' '.join(tokens[1].split('_')).lower()
                if e not in event:
                    print('UNKNOWN event: "%s"' % e)
                else:
                    data[e] = [int(num) for num in tokens[2:]]
            else:
                pass
        if data != {}:
            SportDiary.insert_diary(subject = date, content = repr(data))


    @classmethod
    def draw(cls, x, y, labels):
#        plt.figure(figsize=(8, 8))
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
        