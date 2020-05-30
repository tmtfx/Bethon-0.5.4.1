#  Mm, interesting.  I don't remember doing this, but here it is.
#  Looks like it's pulling the pieces out of a BMessage and making
#  a dictionary.
#
#  See contents.py for a similar function, without the class.
#
import struct
import types
import BMessage

def mkDtp(lst):
	x = {}
	for key, suf in lst:
		x[struct.unpack('l', key)[0]] = suf
	return x

class Message:
	lst = ( ('CSTR', 'String'),
		('BOOL', 'Bool'),
		('DBLE', 'Double'),
		('FLOT', 'Float'),
		('LLNG', 'Int64'),
		('LONG', 'Int32'),
		('SHRT', 'Int16'),
		('BYTE', 'Int8'),
		('MSGG', 'Message'))
	Dtp = mkDtp(lst)
	def __init__(self, *args):
		self.this = apply(BMessage.BMessage, args)
	def __getitem__(self, at):
		if type(at) != types.StringType:
			raise TypeError, at
		try:
			tp, ct = self.this.GetInfo(at)
		except BMessage.error, ev:
			raise KeyError, at
		ret = []
		try:
			tfs = self.Dtp[tp]
		except KeyError:
			raise SystemError, 'no converter for type %x \'%s\'' % (tp, struct.pack('l', tp))
		for i in range(ct):
			ret.append(eval('self.this.Find%s(at, %d)' % (tfs, i)))
		return tuple(ret)
	def __getattr__(self, attr):
		return getattr(self.this, attr)
	def dict(self):
		x = struct.unpack('l', 'ANYT')[0]
		i = 0
		dct = {}
		while 1:
			try:
				nm, tp, ct = self.this.GetInfo(x, i)
			except BMessage.error, ev:
				nm = None
			if nm is None:
				break
			val = []
			tfs = self.Dtp.get(tp)
			if tfs:
				for j in range(ct):
					val.append(eval('self.this.Find%s(nm, %d)' % (tfs, j)))
			else:
				val = [None]*ct
			dct[nm] = tuple(val)
			i = i + 1
		return dct
	def __str__(self):
		return str(self.dict())
