#
#  Wrap tuple data types.
#
#  The types are structs that for economy are rendered in Python as
#  tuples, rather than internal C types.  The code generating module
#  that handles the C logic for this (sgrules) also generates Python
#  code for this wrapper system, so any time that's changed, the
#  wrapper structs module needs to be updated too.
#
#  This module contains the base class for the wrapper structs, and
#  is not generated.  Each derived class supplies a matched pair of
#  class-scope tuples, one naming the members and the other their types.
#  The type name (if any) is looked up and used to generate the data
#  item, on initialization and on assignment.  I think this is probably
#  infrequent, if not it should be optimized.
#

#  If there's a type, look it up and use it to generate the result.
#  This lookup is because I put the types in the class namespace -
#  a reference there to another class can fail if that class is defined
#  below the present class.  There are certainly other ways around this.
#
def tostruct(x, m, t):
	if t:
		return t(x)
	else:
		return x

def fromstruct(x, m, t):
	if t is None:
		return x
	else:
		return x.tuple

class Structuple:
	def __init__(self, t):
		if len(t) != len(self._members):
			raise TypeError, '%d-tuple' % len(t)
		self._types = self.typegen()
		self._dt = map(tostruct, t, self._members, self._types)

	def __getitem__(self, i):
		d = self._dt[i]

		#  Assuming you want tuple result rather than instance,
		#  if you ask via index.
		#
		if type(d) == type(self):
			d = d.tuple
		return d

	def __getattr__(self, a):
		if a == 'tuple':
			return tuple(map(fromstruct,
				self._dt, self._members, self._types))
		for i in range(len(self._dt)):
			if self._members[i] == a:
				return self._dt[i]
		raise AttributeError, a

	def __setattr__(self, a, v):
		if a in ('_dt', '_types'):
			self.__dict__[a] = v
			return
		for i in range(len(self._dt)):
			if self._members[i] == a:
				if type(v) == type(()):
					self._dt[i] = self._types[i](v)
				else:
					self._dt[i] = v
				return
		raise AttributeError, a
	def __str__(self):
		return str(self.tuple)
	def __repr__(self):
		return '<%s: %s>' % (self.__class__.__name__, self.tuple)
