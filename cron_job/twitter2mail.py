#!/usr/local/bin/python
import smtplib
import sys
import feedparser
import urllib2
import simplejson
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from urllib import urlencode
from django.utils.encoding import smart_str, smart_unicode
from datetime import datetime

response = urllib2.urlopen('https://twitter2mail.appspot.com/get_users')
json = response.read()

users = simplejson.loads(json)

fromaddr = 'noreply@twitter2mail.appspot.com'

server = smtplib.SMTP('localhost')

for user in users:
  toaddrs = user['email']
  try: 
    if user['reply_mode'] == 1:
      q = '+to%3A'
    else:
      q = '+%40'
  
    q += user['username']
    d = feedparser.parse('http://search.twitter.com/search.atom?q='+q)

    new_tweets = []

    for item in d['items']:
      if item['published'] > user['last_run']:
        if len(new_tweets) == 0:
          latest_tweet = item['published']
          print '['+str(datetime.now())+'] New tweets for: '+user['username']
        new_tweet = {'username': item['author'].split()[0], 'author': item['author'], 'profile_img_url': item['links'][1]['href'], 'html_content': item['content'][0]['value'], 'link': item['link'], 'published': item['published'], 'text_content': item['title']}

        if len(item['links']) == 3:
          new_tweet['thread'] = item['links'][2]['href'].split('/')[-1].split('.')[0]
        new_tweets.append(new_tweet)

    if len(new_tweets) > 0:
      if not user['digest']:
        for tweet in new_tweets:
          # short the message, if possible
          if tweet['text_content'].find('@'+user['username']) == 0:
            tweet['text_content'] = tweet['text_content'].split('@'+user['username'])[1]
          msg = MIMEText('', 'plain', 'UTF-8')
          msg['To'] = toaddrs
          msg['From'] = '@' + tweet['username'] + '<'+fromaddr+'>'
          msg['Subject'] = tweet['text_content'].encode('UTF-8')
          server.sendmail(fromaddr, toaddrs, msg.as_string())
      else:
        msgRoot = MIMEMultipart('related')
        msgRoot['To'] = toaddrs
        msgRoot['From'] = fromaddr
        msgRoot.preamble = 'This is a multi-part message in MIME format.'
        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)

        html = '<table cellspacing="0" cellpadding="0" border="0" style="margin-left:10px">'
        text = ''

        for tweet in new_tweets:
          html += '<tr style="border-top:1px dashed #ccc"><td style="padding:5px 5px 5px 0"><img title="'+tweet['author']+'" src="'+tweet['profile_img_url']+'"/></td><td style="width:350px;padding-left:5px">'+tweet['html_content']+' <a style="font-size:75%;color:#aaa" href="'+tweet['link']+'">'+tweet['published']+'</a>'

          if tweet.has_key('thread'):
            html += ' <a style="font-size:75%;color:#aaa" href="http://twitter2mail.appspot.com/thread?id='+tweet['thread']+'">View Thread</a>'

          html += '</td></tr>\n'

          text = text + tweet['text_content'] + '\n'
          print 'Tweet = "'+tweet['username']+': '+tweet['published']+'"'

        html += '</table>'
        html += '<p>Delivered to your doorstep by <a href="http://twitter2mail.appspot.com">Twitter2Mail</a> <img height="16" width="16" src="http://twitter2mail.appspot.com/static/t2mail.gif"/></p>'
        text += 'Delivered to your doorstep by http://twitter2mail.appspot.com'

        msgText = MIMEText(text.encode('UTF-8'), 'UTF-8')
        msgAlternative.attach(msgText)

        msgText = MIMEText(html.encode('UTF-8'), 'html', 'UTF-8')
        msgAlternative.attach(msgText)
        msgRoot['Subject'] = 'Recent @replies for '+user['username']+' ('+str(len(new_tweets))+')'

        server.sendmail(fromaddr, toaddrs, msgRoot.as_string())
  
      response = urllib2.urlopen('https://twitter2mail.appspot.com/update?'+urlencode({'username':user['username'],'date':latest_tweet}))
      print 'Email(s) sent for '+user['username']+': '+response.read()
  
  except:
    print "Error compiling/sending email!"
    print sys.exc_info()

server.quit()

