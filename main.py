#encoding:utf-8
import webapp2

from lib.sport_diary import MainPage
from lib.diary import DiaryPage, NewDiaryPage
from lib.user import LogInPage, LogOutPage, SignUpPage

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/diary', DiaryPage),
    ('/newdiary', NewDiaryPage),
    ('/login', LogInPage),
    ('/signup', SignUpPage),
    ('/logout', LogOutPage),
    ], debug = True)
