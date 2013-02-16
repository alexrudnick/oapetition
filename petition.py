import string
import random
import os
import cgi

import webapp2
import jinja2
from google.appengine.ext import db

import signaturecount

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
    activationkey = db.StringProperty()
    activated = db.BooleanProperty()

class MainPage(webapp2.RequestHandler):
    def get(self):
        count = signaturecount.get_count()
        mostrecent = db.GqlQuery("SELECT * "
                                 "FROM Signature "
                                 "WHERE ANCESTOR IS :1 "
                                 "ORDER BY date DESC LIMIT 10",
                                 KEY)
        template_values = {
            'count': count,
            'mostrecent': mostrecent
        }
        self.response.headers['Content-Type'] = 'text/html'
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
                                 "  AND activated = TRUE "
                                 "ORDER BY date DESC",
                                 KEY)
        for signature in signatures:
            template_values['signatures'].append(signature)

        template = jinja_environment.get_template('allsignatures.html')
        self.response.out.write(template.render(template_values))

def generate_activationkey():
    chars = string.ascii_letters
    return "".join(random.sample(chars, 8))

class SignPage(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        template = jinja_environment.get_template('sign.html')
        self.response.out.write(template.render(template_values))

    def post(self):
        signature = Signature(parent=KEY)
        signature.name = self.request.get('name')
        signature.subfield = self.request.get('subfield')
        signature.affiliation = self.request.get('affiliation')
        signature.wontpublish = bool(self.request.get('wontpublish'))
        signature.wontreview = bool(self.request.get('wontreview'))
        signature.wontjoin = bool(self.request.get('wontjoin'))

        signature.activated = False
        signature.activationkey = generate_activationkey()
        signature.put()

        send_confirmation_email(signature)
        self.redirect('/thanks')

class ActivatePage(webapp2.RequestHandler):
    def get(self):
        signaturecount.increment()
        template_values = {}
        template = jinja_environment.get_template('activate.html')
        self.response.out.write(template.render(template_values))

app = webapp2.WSGIApplication([
                               ('/', MainPage),
                               ('/sign', SignPage),
                               ('/activate', ActivatePage),
                               ('/allsignatures', AllSignatures)
                              ], debug=True)
