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
import os
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext import db
from main import User

class StatsHandler(webapp.RequestHandler):

  def get(self):
    q = User.all()
    results = [{'username':u.username, 'email':u.email, 'reply_mode':u.reply_mode, 'last_run':u.last_run.strftime('%Y-%m-%dT%H:%M:%SZ'), 'digest': u.digest} for u in q]
    template_values = {
      'users': results,
      'count': len(results)
    }
    path = os.path.join(os.path.dirname(__file__), 'stats.html')
    self.response.out.write(template.render(path, template_values))
    

def main():
  application = webapp.WSGIApplication([
    ('/admin/stats', StatsHandler)
    ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
