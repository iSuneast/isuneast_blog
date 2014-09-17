import os
import webapp2
import jinja2
import re
import json
import time

from google.appengine.api import memcache
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True, extensions=['jinja2.ext.autoescape'])

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


def get_cache(key):
    return memcache.get(key)


def set_cache(key, value):
    memcache.set(key, value)


def delete_cache(key):
    memcache.delete(key)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class Blogs(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

    def render(self):
        return render_str("blog.html", blog=self)

    def get_content(self):
        blog = {}
        blog['subject'] = str(self.subject)
        blog['content'] = str(self.content)
        blog['created'] = str(self.created)
        return blog


class NewPost(Handler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            blog = Blogs(subject=subject, content=content)
            blog.put()
            get_blogs(True)

            self.redirect('/%s' % str(blog.key().id()))
        else:
            error_subject = ""
            error_content = ""
            if not subject:
                error_subject = "Please input Subject!"
            if not content:
                error_content = "Please input content!"
            self.render("newpost.html", 
                subject=subject, error_subject=error_subject, 
                content=content, error_content=error_content)


def get_blog_by_id(blog_id):
    key = str(blog_id)
    cache = get_cache(key)
    if cache == None:
        blog = Blogs.get_by_id(int(blog_id))
        cache_time = time.time()
        set_cache(key, [blog, cache_time])
    else:
        blog, cache_time = cache
        
    return blog, cache_time


class BlogPage(Handler):
    def get(self, blog_id):
        blog, cache_time = get_blog_by_id(blog_id)
        cache_len = time.time() - cache_time
        self.render("permalink.html", blog=blog, cache_len=cache_len)


class BlogPageJson(Handler):
    def get(self, blog_id):
        self.response.headers['Content-Type'] = 'application/json'
        blog, cache_time = get_blog_by_id(int(blog_id.split('.')[0]))
        j = json.dumps(blog.get_content())
        self.write(j)


def get_blogs(update = False):
    key = 'blogs'
    cache = get_cache(key)
    if cache == None or update:
        blogs = db.GqlQuery("select * from Blogs order by created desc")
        cache_time = time.time()
        set_cache(key, [blogs, cache_time] )
    else:
        blogs, cache_time = cache
    return blogs, cache_time


class MainPage(Handler):
    def get(self):
        blogs, cache_time = get_blogs()
        cache_len = time.time() - cache_time

        self.render("blogs.html", blogs=blogs, cache_len=cache_len)

    def post(self):
        self.redirect("/newpost")


class MainPageJson(Handler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        blogs, cache_time = get_blogs()
        j = json.dumps([blog.get_content() for blog in blogs])
        self.write(j)


class Users(db.Model):
    username = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)


class SignupPage(Handler):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    PWD_RE = re.compile(r"^.{3,20}$")
    EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

    def valid_username(self, username):
        if not self.USER_RE.match(username):
            return "That's not a valid username."
        return ''

    def valid_pwd(self, password, verify_password):
        if not self.PWD_RE.match(password):
            return "That wasn't a valid password."
        elif password != verify_password:
            return "Password don't match"
        return ''

    def valid_email(self, email):
        if email and not self.EMAIL_RE.match(email):
            return "That's not a valid email."
        return ''

    def get(self):
        self.render('signup.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify_password = self.request.get('verify')
        email = self.request.get('email')

        error_name = self.valid_username(username)
        error_pwd = self.valid_pwd(password, verify_password)
        error_email = self.valid_email(email)

        if not (error_name or error_pwd or error_email):
            user = Users(username = username, password = password)
            user.put()

            users = db.GqlQuery('select * from Users')
            for u in users:
                print 'user: ', u.username, u.password

            self.response.headers['Content-Type'] = 'text/plain'
            self.response.headers.add_header('Set-Cookie', str('name=%s; Path=/' % username))
            self.redirect('/welcome')
        else:
            self.render('signup.html', 
                username=username, error_name=error_name,
                error_pwd=error_pwd,
                email=email, error_email=error_email)


class LoginPage(Handler):
    def get(self):
        name = self.request.cookies.get('name')
        self.render('login.html', username=name)

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        error = ''
        if not username:
            error = 'please input Username'
        elif not password:
            error = 'please input Password'
        else:
            user = db.GqlQuery('select * from Users')
            error = 'User doesn\'t exist'
            for u in user:
                if u.username == username:
                    if u.password != password:
                        error = 'Password doesn\'t match'
                    else:
                        error = ''
                    break

        if error == '':
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.headers.add_header('Set-Cookie', str('name=%s; Path=/' % username))
            self.redirect('/welcome')
        else:
            self.render('login.html', username=username, error=error)


class LogoutPage(Handler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.headers.add_header('Set-Cookie', str('name=; Path=/'))
        self.redirect('/signup')


class WelcomePage(Handler):
    def get(self):
        name = self.request.cookies.get('name')
        self.render('welcome.html', username=name)


class FlushCache(Handler):
    def get(self):
        memcache.flush_all()
        self.redirect('/')


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/.json', MainPageJson),
    ('/flush', FlushCache),
    ('/signup', SignupPage),
    ('/login', LoginPage),
    ('/logout', LogoutPage),
    ('/newpost', NewPost),
    ('/welcome', WelcomePage),
    ('/([0-9]*)', BlogPage),
    ('/([0-9]*.json)', BlogPageJson)
], debug=True)
