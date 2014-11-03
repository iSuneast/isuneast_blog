#encoding:utf-8
import json
from google.appengine.ext import db
from lib.utils import Handler, Secure

class Diary(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(required = True)

    def get_subject(self):
        return self.subject

    def get_content(self, raw=False):
        if raw:
            return eval(self.content)
        return eval(self.content).replace('\\\r\n', '').replace('\n', '<br>')

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
        if self.proc_json():
            pass
        elif self.proc_diary_id():
            pass
        else:
            diaries = Diary.all().order('-created')
            self.render('diaries.html', diaries = diaries)

    def proc_json(self):
        q = self.request.get('q')
        if q and q == 'json':
            diaries = Diary.all().order('-created')

            self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
            self.write(json.dumps([diary.as_dict() for diary in diaries],
             ensure_ascii=False))
            
            return True
        return False

    def proc_diary_id(self):
        diary_id = self.request.get('id')
        if diary_id:
            diary = Diary.get_by_id(int(diary_id))
            if diary:
                self.render('diary.html', diary = diary)
                return True
        return False


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
