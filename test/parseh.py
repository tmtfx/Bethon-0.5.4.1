#
#  Gropes out most of the symbols and enums in a Be include file.
#  Just occurs to me as I write this little comment that the standard
#  distribution has some processor for include files, to make SOCKET.py
#  and stuff like that.  Maybe that would work better than this?
#
#  Anyway, see bpygen/symbols for the way I normally do this.
#
import string
import sys
from hollerith import str2int

def issymbol(z):
	if z[0] in string.digits:
		return 0
	for c in z:
		if c in string.letters or c in string.digits or c == '_':
			pass
		else:
			return 0
	return 1

def aslong(z):
	if z[:1] == '\'':
		return str2int(z[1:-1])
	if z[:5] == '(int)':
		z = string.strip(z[5:])
	if z[:2] == '0x':
		base = 16
		z = z[2:]
	else:
		base = 10
	if z[-1:] == 'L':
		z = z[:-1]
	if base == 16 and len(z) == 8:
		xo = string.atoi(z[-2:], 16)
		x = z[:6]
		i = string.atoi(x, 16)
		return (i << 8) | xo
	return string.atoi(z, base)

def intrep(i):
	if i == 0:
		return '0'
	elif i > 255:
		return '0x%x' % i
	elif (i & 0x0f) == 0:
		return '0x%x' % i
	else:
		return '%d' % i

def asfloat(z):
	return string.atof(z)

class Enum:
	def __init__(self, gbl):
		self.i = 0
		self.buf = None
		self.end = 0
		self.name = None;
		self.gbl = gbl
	def next(self, line):
		if self.buf is None:
			x = string.find(line, '{')
			if x >= 0:
				self.buf = line[x + 1:]
				line = line[:x]
			else:
				sys.stderr.write('no { in "%s"\n' % repr(line))
			for x in string.split(line[:x]):
				if x != 'enum':
					self.name = x
		elif self.end:
			v = string.split(line, ';')
			if len(v) > 1:
				return v[1]
		else:
			x = string.find(line, '}')
			if x >= 0:
				self.end = 1
				self.buf = self.buf + line[:x]
				return self.next(line[x + 1:])
			else:
				self.buf = self.buf + line
		return None

	def pr(self):
		b = []
		rest = self.buf
		while 1:
			i = string.find(rest, '/*')
			if i < 0:
				break
			b.append(rest[:i])
			rest = rest[i + 2:]
			i = string.find(rest, '*/')
			if i < 0:
				sys.stderr.write('unbalanced "*/": \"%s\"\n' % repr(rest))
			else:
				rest = rest[i + 2:]
		b.append(rest)
		self.buf = string.join(b, '')
		for expr in string.split(self.buf, ','):
			expr = string.split(expr, '=')
			k = string.strip(expr[0])
			if not issymbol(k):
				sys.stderr.write('\"%s\" is not a symbol.\n' % k)
				break
			if k[:2] != 'B_':
				sys.stderr.write('\"%s\" is not a B_ symbol.\n' % k)
				k = None
			if len(expr) > 1:
				z = string.strip(expr[1])
				if z[:2] == 'B_':
					self.i = self.gbl[z]
					if k:
						print k, '=', z
				else:
					self.i = aslong(z)
					if k:
						print k, '=', intrep(self.i)
			else:
				if k:
					print k, '=', self.i
			if k:
				self.gbl[k] = self.i
			self.i = self.i + 1
		del self.end
		del self.buf

def Symbol(line, gbl):
	v = string.split(line)
	if len(v) == 2 and v[0][:2] == 'B_':
		k, v = v
		r = v
		if v[:1] == '"':
			v = v[1:-1]
		elif string.find(v, '.') >= 0:
			v = asfloat(v)
		else:
			v = aslong(v)
			r = intrep(v)
		print k, '=', r
		gbl[k] = v

def rf(file):
	fp = open(file, 'r')
	n = string.split(file, '/')
	if len(n) > 1:
		n = n[-2] + '/' + n[-1]
	else:
		n = n[-1]
	print '#', n
	nxt = None
	e = None
	lnum = 0
	while 1:
		if nxt is None:
			line = fp.readline()
			if not line:
				break
			lnum = lnum + 1
		else:
			line = nxt
			nxt = None
		if e is None:
			if line[:7] == '#define':
				try:
					Symbol(line[7:], gbl)
				except:
					print '# Error line', lnum
				continue
			elif string.find(line, 'enum') >= 0:
				e = Enum(gbl)
			else:
				continue
		nxt = e.next(line)
		if nxt is None:
			pass
		else:
			try:
				e.pr()
			except:
				print '# Error line', lnum
			e = None
	fp.close()

gbl = {}
for file in sys.argv[1:]:
	rf(file)
