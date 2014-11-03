#encoding:utf-8
import webapp2
from lib.utils import Handler
from lib.exercise import ExercisePage
from lib.diary import DiaryPage, NewDiaryPage
from lib.user import LogInPage, LogOutPage, SignUpPage

class MainPage(Handler):
    def get(self):
        self.render('main.html')

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/diary', DiaryPage),
    ('/exercise', ExercisePage),    
    ('/newdiary', NewDiaryPage),
    ('/login', LogInPage),
    ('/signup', SignUpPage),
    ('/logout', LogOutPage),
    ], debug = True)
