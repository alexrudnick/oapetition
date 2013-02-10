import webapp2
import jinja2
import os
from google.appengine.api import users

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class Signer:
    def __init__(self, name, subfield=None, affiliation=None):
        self.name = name
        self.subfield = subfield
        self.affiliation = affiliation

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        template_values = {
            'count': 100,
            'mostrecent': [
                Signer("Todd Todderson", "MLP", "University of Foo"),
                Signer("Nancy McFoo", "LP", "University of Bar"),
                Signer("Ilsa McFoo", "PR", "FooCorp"),
            ],
        }
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))


class SignPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        template_values = {}
        template = jinja_environment.get_template('sign.html')
        self.response.out.write(template.render(template_values))

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/sign', SignPage)], debug=True)
