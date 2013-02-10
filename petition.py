import webapp2
import jinja2
import os
import cgi
from google.appengine.api import users
from google.appengine.ext import db

KEY = db.Key.from_path("OAPETITION", "OAPETITION")

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class Signature(db.Model):
    name = db.StringProperty()
    subfield = db.StringProperty()
    affiliation = db.StringProperty()
    wontpublish = db.BooleanProperty()
    wontreview = db.BooleanProperty()
    wontjoin = db.BooleanProperty()
    date = db.DateTimeProperty(auto_now_add=True)

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        mostrecent = db.GqlQuery("SELECT * "
                                 "FROM Signature "
                                 "WHERE ANCESTOR IS :1 "
                                 "ORDER BY date DESC LIMIT 10",
                                 KEY)
        template_values = {
            'count': 100,
            'mostrecent': mostrecent
        }
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))

class AllSignatures(webapp2.RequestHandler):
    def get(self):
        template_values = {
            'count': 100,
            'signatures': [],
        }
        signatures = db.GqlQuery("SELECT * "
                                 "FROM Signature "
                                 "WHERE ANCESTOR IS :1 "
                                 "ORDER BY date DESC",
                                 KEY)
        for signature in signatures:
            template_values['signatures'].append(signature)

        template = jinja_environment.get_template('allsignatures.html')
        self.response.out.write(template.render(template_values))

class SignPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        template_values = {}
        template = jinja_environment.get_template('sign.html')
        self.response.out.write(template.render(template_values))

    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url('/sign'))
        signature = Signature(parent=KEY)
        signature.name = self.request.get('name')
        signature.subfield = self.request.get('subfield')
        signature.affiliation = self.request.get('affiliation')
        signature.wontpublish = self.request.get('wontpublish') or False
        signature.wontreview = self.request.get('wontreview') or False
        signature.wontjoin = self.request.get('wontjoin') or False
        signature.put()
        self.redirect('/?thanks')

app = webapp2.WSGIApplication([
                               ('/', MainPage),
                               ('/sign', SignPage),
                               ('/allsignatures', AllSignatures)
                              ], debug=True)
