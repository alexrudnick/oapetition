import string
import random
import os
import cgi
import re

import webapp2
import jinja2
from google.appengine.api import mail
from google.appengine.ext import db

import signaturecount

KEY = db.Key.from_path("OAPETITION", "OAPETITION")

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class Signature(db.Model):
    name = db.StringProperty()
    email = db.StringProperty()
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
                                 "  AND activated = TRUE "
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

EMAIL_TEMPLATE = u"""\
Dear {0},

Please click the following link to activate your signature on
teardownthispaywall!

{1}

Thank you so much!

-- 
-- teardownthispaywall
-- http://teardownthispaywall.appspot.com
"""

def send_confirmation_email(signature):
    """Send an email with the activation link."""
    name = signature.name
    message = mail.EmailMessage(
        sender="teardownthispaywall <noreply@teardownthispaywall.appspot.com>",
        subject="teardownthispaywall: signature activation link")
    url = "http://teardownthispaywall.appspot.com/activate?id={0}&key={1}"
    url = url.format(signature.key().id(), signature.activationkey)
    message.to = signature.email
    message.body = EMAIL_TEMPLATE.format(name, url)
    message.send()

## simple check based on http://stackoverflow.com/questions/8022530/
email_pat = re.compile(r"[^@]+@[^@]+\.[^@]+$")
def validate_signature(name, email, affiliation, subfield):
    return (email_pat.match(email) and
            len(name) in range(1, 81) and
            len(affiliation) in range(81) and
            len(subfield) in range(81))

class SignPage(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        template = jinja_environment.get_template('sign.html')
        self.response.out.write(template.render(template_values))

    def post(self):
        name = self.request.get('name')
        subfield = self.request.get('subfield')
        email = self.request.get('email')
        affiliation = self.request.get('affiliation')
        wontpublish = bool(self.request.get('wontpublish'))
        wontreview = bool(self.request.get('wontreview'))
        wontjoin = bool(self.request.get('wontjoin'))

        validated = validate_signature(name, email, affiliation, subfield)
        if not validated:
            self.redirect('/sign?notquiteright')
            return
        signature = Signature(parent=KEY,
                              name = name,
                              subfield = subfield,
                              email = email,
                              affiliation = affiliation,
                              wontpublish = wontpublish,
                              wontreview = wontreview,
                              wontjoin = wontjoin,
                              activated = False,
                              activationkey = generate_activationkey())
        signature.put()
        send_confirmation_email(signature)
        self.redirect('/thanks')

def activate_signature(signature_id, activationkey):
    """Try to pull up a signature with the specified id; if the activation key
    matches, activate it, increment the count of active signatures,  and return
    True! False otherwise."""
    try:
        signature = Signature.get_by_id(int(signature_id), parent=KEY)
        if signature.activationkey == activationkey:
            signature.activated = True
            signature.put()
            signaturecount.increment()
            return True
    except:
        pass
    return False

class ActivatePage(webapp2.RequestHandler):
    def get(self):
        ## try to activate the signature...
        signature_id = self.request.get('id')
        activationkey = self.request.get('key')
        activated = activate_signature(signature_id, activationkey)
        if activated:
            message = \
"Great! Your signature has been activated! Thank you so much for signing!"
        else:
            message = \
"Couldn't activate that signature with that activation code, sorry!"
        template_values = {'message': message}
        template = jinja_environment.get_template('activate.html')
        self.response.out.write(template.render(template_values))

app = webapp2.WSGIApplication([
                               ('/', MainPage),
                               ('/sign', SignPage),
                               ('/activate', ActivatePage),
                               ('/allsignatures', AllSignatures)
                              ], debug=True)
