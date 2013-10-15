# System
from time import gmtime, strftime
import calendar, datetime
import cgi
import execjs
import json
import time
import os
import re

RE_PRE_SPACE_START = re.compile('(?P<tag><pre[^>]*>)\s*')
RE_PRE_SPACE_END = re.compile('\s*(?P<tag></pre>)')
RE_XMP_START = re.compile('<xmp')
RE_XMP_END = re.compile('</xmp>')
RE_DEFER = re.compile('(?P<before><[a-z][a-z0-9]*)\s+defer\s*(?P<after>[^>]*>)')
RE_CODE = re.compile(r"<code>(?P<code>.*?)</code>", re.DOTALL)



def code_escape(match):
  return '<code>\n%s\n\n</code>' % cgi.escape(match.group('code'))

THEMES =  [
  'beige',
  'default',
  'moon',
  'night',
  'serif',
  'simple',
  'sky',
  'solarized',
]

HTML = '''
<!doctype html>
<html>
  <head>
    <base target="_new" />
    <meta charset="utf-8">
    <title>Slide</title>
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link rel="stylesheet" href="/node_modules/reveal.js/css/reveal.css" />
    <link rel="stylesheet" href="/node_modules/reveal.js/css/theme/default.css" id="theme" />
    <link rel="stylesheet" href="/node_modules/reveal.js/lib/css/zenburn.css" />
    <link rel="stylesheet" href="/src/style.css" />
    <!--[if lt IE 9]>
    <script src="/node_modules/reveal.js/lib/js/html5shiv.js"></script>
    <![endif]-->
  </head>

  <body>
    <div class="reveal">
      <div class="slides">
      %(body)s
      </div>
    </div>

    <script src="/node_modules/reveal.js/lib/js/head.min.js"></script>
    <script src="/node_modules/reveal.js/js/reveal.min.js"></script>
    <script>

      // Full list of configuration options available here:
      // https://github.com/hakimel/reveal.js#configuration
      Reveal.initialize({
        controls: true,
        progress: true,
        history: true,
        center: true,

        theme: Reveal.getQueryHash().theme, // available themes are in /css/theme
        transition: Reveal.getQueryHash().transition || 'default', // default/cube/page/concave/zoom/linear/fade/none

        // Optional libraries used to extend on reveal.js
        dependencies: [
          { src: '/node_modules/reveal.js/lib/js/classList.js', condition: function() { return !document.body.classList; } },
          { src: '/node_modules/reveal.js/plugin/markdown/marked.js', condition: function() { return !!document.querySelector( '[data-markdown]' ); } },
          { src: '/node_modules/reveal.js/plugin/markdown/markdown.js', condition: function() { return !!document.querySelector( '[data-markdown]' ); } },
          { src: '/node_modules/reveal.js/plugin/highlight/highlight.js', async: true, callback: function() { hljs.initHighlightingOnLoad(); } },
          { src: '/node_modules/reveal.js/plugin/zoom-js/zoom.js', async: true, condition: function() { return !!document.body.classList; } },
          { src: '/node_modules/reveal.js/plugin/notes/notes.js', async: true, condition: function() { return !!document.body.classList; } }
        ]
      });
    </script>
  </body>
</html>
'''

HTML_NOT_FOUND = '''
<!doctype html>
<html>
<body>
  <h1>View Slides</h1>
  <ul>
    <li><a href="/keynotes">keynotes</a></ii>
  </ul>
</body>
</html>
'''

_supported_file_type = {
  'css': 'text/css',
  'gif': 'image/gif',
  'html': 'text/html',
  'ico': 'image/vnd.microsoft.icon',
  'jpg': 'image/jpg',
  'js': 'application/javascript',
  'png': 'image/png',
  'woff': 'application/x-font-woff',
  'ttf': 'application/octet-stream',
  'svg': 'image/svg+xml'
}

_text_cache = {}

def read_text(path, text_cache = None) :
  key = '_%s_%s' % (path , str(os.path.getmtime(path)))
  if key in _text_cache:
    return _text_cache[key]

  try :
    f = open(path)
    content = f.read()
    f.close()
    _text_cache[key] = content
    return content
  except Exception as e :
    error('Unable to read file', path)
    raise e


def get_request_file_type(path):
  idx = path.find('?')
  if idx > -1:
    path = path[0:idx]
  idx = path.rfind('.')
  if idx > -1:
    path = path[idx + 1:]
  if path in _supported_file_type:
    return path
  else:
    return None

def handle_get(path, query_params):
  content = ''
  file_type = get_request_file_type(path)
  mime = _supported_file_type.get(file_type)
  slide_path = './slides/' + path + '.html'

  if os.path.isfile(slide_path):
    mime  = 'text/html'
    body = read_text(slide_path)
    sections = []
    for section in body.split('==='):
      section = section.strip()
      if section:
        if section.find('>>>') > -1:
          levels = []
          for level in section.split('>>>'):
            levels.append('<section><!--level-->\n' + level + '\n</section>')
          section = '\n\n\n'.join(levels)
        sections.append('<section><!--slide-->\n' + section + '\n</section>')

    body = '\n\n\n'.join(sections)
    body = RE_XMP_START.sub('<pre ', body)
    body = RE_XMP_END.sub('</pre>', body)
    body = RE_PRE_SPACE_START.sub(r'\g<tag><code>', body)
    body = RE_PRE_SPACE_END.sub(r'</code>\g<tag>', body)
    body = RE_CODE.sub(code_escape, body)
    body = RE_DEFER.sub(r'\g<before> class="fragment" \g<after>', body)
    content = HTML % {
      'body': body
    }
  elif mime and os.path.isfile('.' + path):
    content = read_text('.' + path)
  else:
    content = HTML_NOT_FOUND % {
      'path': cgi.escape(path)
    }
    mime = 'text/html'

  return {
    'mime': mime,
    'content': content
  }
