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


class BlogHandler(Handler):
    def render(self, template, **kw):
        login_name = self.request.cookies.get('name')
        wiki_url = self.request.url.split('/')[-1]
        super(BlogHandler, self).write(self.render_str(template, login_name=login_name, wiki_url=wiki_url, **kw))


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


class NewPost(BlogHandler):
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


class BlogPage(BlogHandler):
    def get(self, blog_id):
        blog, cache_time = get_blog_by_id(blog_id)
        cache_len = time.time() - cache_time
        self.render("permalink.html", blog=blog, cache_len=cache_len)


class BlogPageJson(BlogHandler):
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


class MainPage(BlogHandler):
    def get(self):
        blogs, cache_time = get_blogs()
        cache_len = time.time() - cache_time

        self.render("blogs.html", blogs=blogs, cache_len=cache_len)

    def post(self):
        self.redirect("/newpost")


class MainPageJson(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        blogs, cache_time = get_blogs()
        j = json.dumps([blog.get_content() for blog in blogs])
        self.write(j)


class Users(db.Model):
    username = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)


class SignupPage(BlogHandler):
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


class LoginPage(BlogHandler):
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


class LogoutPage(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.headers.add_header('Set-Cookie', str('name=; Path=/'))
        self.redirect('/signup')


class WelcomePage(BlogHandler):
    def get(self):
        name = self.request.cookies.get('name')
        self.render('welcome.html', username=name)


class FlushCache(BlogHandler):
    def get(self):
        memcache.flush_all()
        self.redirect('/')


class Wikis(db.Model):
    content = db.TextProperty(required = True)
    url = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)


def get_wiki_by_url(wiki_url, created = None, fetch_all = False):
    wikis = Wikis.all().order('-created')
    ret = []
    for wiki in wikis:
        if wiki.url == wiki_url:
            ret.append(wiki)
            if created is not None and str(wiki.created) == created:
                return wiki
    if fetch_all:
        return ret
    elif len(ret) > 0:
        return ret[0]


class WikiPage(BlogHandler):
    def get(self, wiki_url):
        created = self.request.get('created')
        wiki = get_wiki_by_url(wiki_url, created=created)
        if wiki is None:
            self.redirect('/_edit%s' % wiki_url)
        else:
            self.render('wiki.html', wiki=wiki)


class EditPage(BlogHandler):
    def get(self, wiki_url):
        name = self.request.cookies.get('name')
        if name is None or name is '':
            self.redirect('/')
            return

        created = self.request.get('created')
        wiki = get_wiki_by_url(wiki_url, created=created)
        content = ''
        if wiki is not None:
            content = wiki.content
        self.render('newwiki.html', content=content)

    def post(self, wiki_url):
        content = self.request.get('content')
        if content:
            wiki = Wikis(content=content, url=wiki_url)
            wiki.put()

            self.redirect('%s' % wiki_url)
        else:
            error_content = "Please input content!"
            self.render("newwiki.html",
                content=content, error_content=error_content)


class HistoryPage(BlogHandler):
    def get(self, wiki_url):
        name = self.request.cookies.get('name')
        if name is None or name is '':
            self.redirect('/')
            return

        wikis = get_wiki_by_url(wiki_url, fetch_all=True)
        content = ''
        self.render('history.html', wikis=wikis)

    def post(self, wiki_url):
        content = self.request.get('content')
        if content:
            wiki = Wikis(content=content, url=wiki_url)
            wiki.put()

            self.redirect('%s' % wiki_url)
        else:
            error_content = "Please input content!"
            self.render("newwiki.html",
                content=content, error_content=error_content)


PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'

application = webapp2.WSGIApplication([
    ('/signup', SignupPage),
    ('/login', LoginPage),
    ('/logout', LogoutPage),

    ('/welcome', WelcomePage),

    ('/_edit' + PAGE_RE, EditPage),
    ('/_history' + PAGE_RE, HistoryPage),
    (PAGE_RE, WikiPage),
], debug=True)
