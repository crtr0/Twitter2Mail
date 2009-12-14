#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import wsgiref.handlers
import logging
from datetime import datetime
import sys
import random
from google.appengine.api import mail
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import urlfetch

from django.utils import simplejson

class User(db.Model):
  username = db.StringProperty(required=True)
  email = db.StringProperty(required=True)  
  reply_mode = db.IntegerProperty(required=True)
  token = db.StringProperty()
  verified = db.BooleanProperty()
  digest = db.BooleanProperty()
  last_run = db.DateTimeProperty(auto_now_add=True)

class UserHandler(webapp.RequestHandler):

  def get(self):
    username = self.request.get('username')
    email = self.request.get('email')
    reply_mode = int(self.request.get('reply_mode'))
    digest = (self.request.get('digest') == 'yes')
    out = {}
        
    try:
       user = User.get_by_key_name('t_'+username)
       if user is None:
         chars = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
           
         while (True):
           token = ''
           for i in range(1,32):
             token += chars[random.randint(0, len(chars)-1)]
           if User.all().filter('token =', token).count() == 0:
             break
           
         user = User(key_name='t_'+username, username=username, email=email, reply_mode=reply_mode, token=token, digest=digest)
         user.put()
           
         # send email with token
         mail.send_mail(sender="Twitter2Mail <carter.rabasa@gmail.com>",
            to=email,
            subject="[Twitter2Mail] Please Verify Your Account",
            body="Please verify your email by going to: https://twitter2mail.appspot.com/verify?token="+token)           
           
         out['message'] = 'A verification email has been sent. Just click on the link in the email!'
       else:
         out['message'] = 'Account already exists!'
       
    except:
      logging.error(sys.exc_info())
      out['message'] = 'Unknown Error'
      
    self.response.out.write(simplejson.dumps(out))

class GetUsersHandler(webapp.RequestHandler):

  def get(self):
    q = User.all().filter('reply_mode >', 0).filter('verified =', True)
    results = [{'username':u.username, 'email':u.email, 'reply_mode':u.reply_mode, 'last_run':u.last_run.strftime('%Y-%m-%dT%H:%M:%SZ'), 'digest': u.digest} for u in q]
    self.response.out.write(simplejson.dumps(results))
    
class UpdateHandler(webapp.RequestHandler):

  def get(self):
    username = self.request.get('username')
    last_run = datetime.strptime(self.request.get('date'), '%Y-%m-%dT%H:%M:%SZ')
    out = {}
    try:    
       user = User.get_by_key_name('t_'+username)
       if user is not None:
         user.last_run = last_run
         user.put()
         out['message'] = 'success'
    except:
      logging.error(sys.exc_info())
      out['message'] = 'Unknown Error'
      
    self.response.out.write(simplejson.dumps(out))

class VerifyHandler(webapp.RequestHandler):

  def get(self):
    token = self.request.get('token')
    try:    
       user = User.all().filter('token =', token).get()
       if user is not None:
         user.verified = True
         user.put()
         message = 'Your are verified! You can close this window.'
       else:
         message = 'Invalid token. Did you copy the entire URL from your email?'       
    except:
      logging.error(sys.exc_info())
      message = 'Unknown Error'
      
    self.response.out.write(message)

class UnsubHandler(webapp.RequestHandler):

  def get(self):
    email = self.request.get('email')
    username = self.request.get('username')

    out = {'success':True}
    try:    
       user = User.all().filter('email =', email).filter('username =', username).get()
       if user is not None:
         mail.send_mail(sender="Twitter2Mail <carter.rabasa@gmail.com>",
            to=email,
            subject="[Twitter2Mail] Delete Your Account",
            body="Delete your account by going to: https://twitter2mail.appspot.com/delete?token="+user.token)           

         out['message'] = 'Email sent! Just click on the link in the email.'
       else:
         out['message'] = 'Error: no matching email/username in system'       
         out['success'] = False
    except:
      logging.error(sys.exc_info())
      out['message'] = 'Unknown Error'
      out['success'] = False
      
    self.response.out.write(simplejson.dumps(out))
    
class DeleteHandler(webapp.RequestHandler):

  def get(self):
    token = self.request.get('token')
    try:    
       user = User.all().filter('token =', token).get()
       if user is not None:
         user.delete()
         message = 'Your account has been deleted! You can close this window.'
       else:
         message = 'Invalid token. Did you copy the entire URL from your email?'       
    except:
      logging.error(sys.exc_info())
      message = 'Unknown Error'
      
    self.response.out.write(message)

class ThreadHandler(webapp.RequestHandler):

  def get(self):
    try:
      thread = self.request.get('thread')
      resp = urlfetch.fetch('http://search.twitter.com/search/thread/'+thread, payload={}, method=urlfetch.GET, headers={}).content
    except:
      logging.error(sys.exc_info())
      resp = 'error'
      
    self.response.out.write(simplejson.dumps(resp))

#class FooHandler(webapp.RequestHandler):
#  def get(self):
#    q = User.all()
#    for u in q:
#      u.digest = True
#      u.put()
#    self.response.out.write("success")
    

def main():
  application = webapp.WSGIApplication([
#    ('/foo', FooHandler),
    ('/user', UserHandler),
    ('/thread_content', ThreadHandler),
    ('/verify', VerifyHandler),
    ('/unsub', UnsubHandler),
    ('/delete', DeleteHandler),
    ('/get_users', GetUsersHandler),
    ('/update', UpdateHandler)
    ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
