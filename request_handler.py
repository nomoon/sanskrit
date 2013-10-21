"""The class that actually handles the input verse."""

import cgi
import StringIO
import sys

import webapp2

import sscan

MAIN_PAGE_HTML = """\
<html>
  <body>
    <form action="/identify" method="post">
      <div><textarea name="input_verse" rows="6" cols="80"></textarea></div>
      <div><input type="submit" value="Identify verse"></div>
    </form>
  </body>
</html>
"""


class InputPage(webapp2.RequestHandler):
  def get(self):
    self.response.write(MAIN_PAGE_HTML)


class IdentifyPage(webapp2.RequestHandler):
  def post(self):
    """What to do with the posted input string (verse)."""
    self.response.write('<html><body>You wrote:<pre>')
    input_verse = self.request.get('input_verse')
    self.response.write(cgi.escape(input_verse))
    self.response.write('\n\n\n')
    # TODO(shreevatsa): Get rid of this hack for capturing stdout.
    stdout_original = sys.stdout
    stdout_new = StringIO.StringIO()
    sys.stdout = stdout_new
    # TODO(shreevatsa): Ridiculous that this runs each time; needs fixing (easy)
    sscan.InitializeData()
    sscan.IdentifyFromLines(input_verse.split('\n'))
    output = stdout_new.getvalue()
    self.response.write(output)
    sys.stdout = stdout_original
    self.response.write('</pre></body></html>')


application = webapp2.WSGIApplication([
    ('/', InputPage),
    ('/identify', IdentifyPage),
], debug=True)
