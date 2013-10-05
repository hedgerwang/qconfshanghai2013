#!/usr/bin/env python

# System
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from os import curdir, sep
import BaseHTTPServer
import CGIHTTPServer
import os
import socket
import string, cgi, time
import sys
import urlparse

# Lib
import app_config
import webserver_util

app_config_path = (
  os.path.dirname(app_config.__file__) + '/app_config.py'
)

webserver_util_path = (
  os.path.dirname(webserver_util.__file__) + '/webserver_util.py'
)

app_config_update_time = os.path.getmtime(app_config_path)
webserver_util_update_time = os.path.getmtime(webserver_util_path)

def get_local_ip_address(target):
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect((target, 8000))
  ipaddr = s.getsockname()[0]
  s.close()
  return ipaddr

def should_refresh():
  global app_config_update_time
  app_config_update_time_2 = os.path.getmtime(app_config_path)
  if app_config_update_time != app_config_update_time_2:
    return True

  global webserver_util_update_time
  webserver_util_update_time_2 = os.path.getmtime(webserver_util_path)
  if webserver_util_update_time != webserver_util_update_time_2:
    # webserver_util_update_time = webserver_util_update_time_2
    return True

  print 'app_config_update_time_2=' + str(app_config_update_time_2)
  print 'webserver_util_update_time_2' + str(webserver_util_update_time_2)
  return False

class WebHandler(BaseHTTPRequestHandler) :
  def do_GET(self) :
    mine = 'text/plain'
    content = ''
    try:
      parsed_url = urlparse.urlparse(self.path)
      query_params = urlparse.parse_qs(parsed_url.query)
      data = webserver_util.handle_get(self.path, query_params)
      mine = data.get('mime')
      content = data.get('content')
    except Exception as error :
      self.send_error(404, 'File Not Found: "%s"' % str(error.message))

    self.send_response(200)
    self.send_header('Content-type', mine)
    self.end_headers()
    self.wfile.write(content)

    if should_refresh():
      print '-' * 80
      print 'Soft Refresh Web Server from version "%s"' % app_config.VERSION
      print '-' * 80
      reload(app_config)
      reload(webserver_util)

  def do_POST(self) :
    raise Exception('NO POST FOR NOW')

def main() :
  try :
    # port must not be smaller than 1024
    server = HTTPServer(('', app_config.PORT), WebHandler)
    print 'started httpserver...\n\nhttp://%s:%s' % (
      get_local_ip_address('www.google.com'),
      app_config.PORT
    )
    server.serve_forever()
  except KeyboardInterrupt :
    print '^C received, shutting down server'
    server.socket.close()

if __name__ == '__main__' :
  main()
