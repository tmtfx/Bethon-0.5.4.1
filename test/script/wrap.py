#  wrap function binds instance with a BeOS API object.  Objects
#  that support this operation can call Python bound methods from
#  their virtual function ``hooks'', so things like MessageReceived()
#  work in Python.
#
class WrapThis:
	def wrap(self, this):
		self.this = this
		self.this.bind(self)
	# def __getattr__(self, name):
	#  This could be neat feature, but occasional pathological
	#  recursive lookup is quite unpleasant.  If it were enabled,
	#  makes self.AddChild work for self.this.AddChild
	# 	return getattr(self.this, name)
	def __repr__(self):
		return '<wrap: %s>' % repr(self.this)
