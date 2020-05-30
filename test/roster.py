import BApplication
import BRoster
import bstructs

class Waiter(BApplication.BApplication):
	def __init__(self):
		BApplication.BApplication.__init__(self, 'application/x-stuff')
	def ReadyToRun(self):
		print self.GetAppInfo()
		r = BRoster.be_roster
		print r.GetActiveAppInfo()
		for a in r.GetAppList():
			try:
				z = r.GetRunningAppInfo(a)
				z = bstructs.app_info(z)
				print z.ref.name
			except BRoster.error, val:
				print 'no luck with team', a
		self.Quit()

w = Waiter()
w.Run()
