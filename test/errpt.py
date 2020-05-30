import BApplication
from BAlert import BAlert
import string
import traceback
from AppKit import B_QUIT_REQUESTED

class LastChanceLooper:
	def lastchance(self, et, ev, tb):
		st = string.join(traceback.format_exception(et, ev, tb), '')[:-1]
		a = BAlert('Python exception', st, 'This Python application has raised the above fatal exception, exit at your convenience', None, None, 2, 4)
		a.Go()
		# BApplication.be_app.PostMessage(B_QUIT_REQUESTED)
		# BApplication.be_app.Lock()
		# BApplication.be_app.Quit()
