#
#  Hand coded extensions of bstructs automatic tuple wrapper classes.
#
from bstructs import *

auto_BRect = BRect
class BRect(auto_BRect):
	def Height(self):
		return self.right - self.left
	def Width(self):
		return self.bottom - self.top
