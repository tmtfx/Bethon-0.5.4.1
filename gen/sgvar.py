#  Copyright 2001 by Donn Cave, Seattle, Washington, USA.
#  All rights reserved.  Permission to copy, modify and distribute this
#  material is hereby granted, without fee, provided that the above
#  copyright notice appear in all copies.
#
#  Analysis of variables, parameters, types.

from sgcf import cf
import re

class UnsupportedError(Exception):
	pass

#
#  C types used in the present module.
#
class Types:
	cache = {}
	def __init__(self, rule):
		self.rule = rule
		self.name = rule.name
		Types.cache[self.name] = self
		self.have_p2c = 0
		self.have_c2p = 0
	def setup_p2c(self, full):
		#
		#  Generate a function to extract a variable of this type
		#  from its Python analogue.
		#
		if self.have_p2c:
			return
		if not full:
			#  For function returns, which don't need the
			#  InputParam stuff.
			xf = cf.files.xfuns
			oldfile = cf.cfile.setfile(xf)
			self.rule.pretpgen()
			cf.cfile.setfile(oldfile)
			return
		self.have_p2c = 1
		xf = cf.files.xfuns
		oldfile = cf.cfile.setfile(xf)
		self.rule.pretpgen()
		# xf.iput('static const char %s_rep[] = "%s";\n' % (self.name, self.rule.ptype))
		xf.iput('static int\n')
		xf.iput('%s_p2c(struct InputParam *p, PyObject *a)\n' % self.name)
		xf.iput('{\n')
		xf.indent(1)
		xf.iput('%s spud;\n' % self.rule.vtype)
		v = Variable(self.rule.vtype, 'spud')
		p = Variable('PyObject*', 'a')
		self.rule.p2c(p, v)
		if self.rule.makepointer:
			xf.iput('**((%s **) p->var) = spud;\n' % self.rule.vtype)
		else:
			xf.iput('*((%s *) p->var) = spud;\n' % self.rule.vtype)
		xf.iput('return 1;\n')
		xf.indent(-1)
		xf.iput('}\n')
		cf.cfile.setfile(oldfile)

#
#  Static, module scoped variables used for default values.
#
class ModuleStatics:
	def __init__(self):
		self.col = {}
		self.ind = 0
	def mkvalue(self, type, val):
		#
		#  Check for already existing variable with required
		#  type and value.
		#
		fval = '(%s) %s' % (type, val)
		var = self.col.get(fval)
		if not var:
			xf = cf.files.xfuns
			var = Variable(type, 'defVar%d' % self.ind)
			self.col[fval] = var
			self.ind = self.ind + 1
			xf.put('\n')
			decl = var.declare()
			xf.iput('static %s = %s;\n\n' % (
				decl[0], fval))
			var.value = val
		return var

class Expression:
	AUTO = 'auto'
	CTBL = 'ctbl'
	HEAP = 'heap'
	EXPR = 'expr'

class Literal(Expression):
	def __init__(self, value):
		self.value = value
		self.storage = self.EXPR
	def val(self):
		return self.value
	def __str__(self):
		return self.value
	def __repr__(self):
		return '<%s %s>' % (self.__class__.__name__, repr(self.value))

class Variable(Expression):
	def __init__(self, typedesc, name = None):
		self.type = typedesc
		if name:
			self.name = name

		self.ptrcount = 0
		while typedesc[-1:] == '*':
			self.ptrcount = self.ptrcount + 1
			typedesc = typedesc[:-1]

		s = typedesc.split(None, 1)
		if s[0] == 'const':
			self.const = 1
			typedesc = s[1]
		else:
			self.const = 0
		self.basetype = typedesc
		self.storage = self.AUTO
		self.auxptr = 0
		self.dim = None
		self.fromctbl = 0
	def allocate(self, xf, dim):
		if self.fromctbl:
			self.storage = self.HEAP
			xf.iput('%s = new %s();\n' % (self.name, self.basetype))
			return [self.name]
		elif dim:
			self.storage = self.HEAP
			xf. iput('%s = (%s) malloc(%s);\n' % (self.name, self.type, dim))
			return [self.name]
		else:
			return []
	def ampersand(self):
		if not self.dim and not self.ptrcount and self.rule.storage == self.CTBL:
			#  A BEntry, for example, initialized by the
			#  C++ API function and to be returned as a
			#  Python object.  So this is a case of heap
			#  storage where the Python API function is
			#  not to free the object but rather return it.
			#  .dx notation will be &BEntry%...
			#  BMessenger is conventionally passed by value,
			#  so it won't get here.
			#
			self.fromctbl = 1
			self.type = self.type + '*'
			self.ptrcount = self.ptrcount + 1
		if self.rule.storage == self.HEAP:
			#  Caller must allocate this one dynamically, for
			#  whatever reason - probably because size is known
			#  at run time - and the .dx notation isn't the right
			#  place to decide that the variable should therefore
			#  be a pointer.
			if not self.ptrcount:
				self.type = self.type + '*'
				self.ptrcount = self.ptrcount + 1
			self.storage = self.HEAP
	def c2p(self, p, dim = None):
		self.typo.rule.c2p(self, p, dim)

	def classify(self, rule = None, ptrcount = None):
		#
		#  Locate the appropriate rules for this type.
		#  rule and ptrcount parameters are used with
		#  internally generated variables, where the
		#  rule is already known.
		#
		if rule:
			self.rule = rule
		else:
			try:
				self.rule = cf.rules.query(self.basetype)
			except KeyError:
				print repr(self), repr(self.basetype)
				raise UnsupportedError(self.basetype)
		self.typo = Types.cache.get(self.rule.name)
		if not self.typo:
			self.typo = Types(self.rule)
		if self.rule.makepointer and ptrcount is None:
			#  May take value of (its_type *) 0, so for
			#  convenience, might as well create an auxiliary
			#  pointer variable for it.
			self.auxptr = 1

			#  And if it was specified like "entry_ref*",
			#  reduce the pointer - this variable is to be
			#  declared "entry_ref", and that was just a
			#  notational convenience.
			#  The ptrcount parameter allows the caller
			#  to override this whole gimmick because
			#  some internal variables will in fact be
			#  pointers.

			if self.ptrcount:
				self.ptrcount = self.ptrcount - 1
				self.type = self.basetype
	def free(self, xf):
		if self.fromctbl:
			xf.iput('// from CTbl - do not free(%s);\n' % self.name);
		#  (xxx -- is second condition necessary?)
		elif self.storage == self.HEAP and not hasattr(self.dim, 'value'):
			xf.iput('free(%s);\n' % self.name)
	def declare(self):
		#  Return a declaration for the variable - and also
		#  for its auxiliary if any.  Hence a list, not a
		#  string.
		#
		#  Most variables will already have a type classification
		#  (default variables won't), and one or two of the rules
		#  has its own declare function, like BList.
		#
		if hasattr(self, 'typo') and hasattr(self.typo.rule, 'declare'):
			return self.typo.rule.declare(self)

		if self.dim:
			dim = self.dim
			if self.storage == self.AUTO:
				if hasattr(dim, 'pos'):
					dim = dim.var
				dim = '[%s]' % dim
			else:
				dim = self.dim
		else:
			dim = ''
		me = '%s %s%s' % (self.type, self.name, dim)
		if self.auxptr:
			aux = '%s *%s = &%s' % (self.type, 'p' + self.name, self.name)
			return [me, aux]
		else:
			return [me]
	def p2c(self, p):
		self.typo.rule.p2c(p, self)
	def passout(self, typedesc, pref, ref, field):
		#
		#  Return this variable as it would appear as a
		#  function argument, given the passing semantics
		#  supplied by the caller (presumably a Parameter.)
		#
		if ref == 'dup':
			return '(%s ? new %s(*%s) : 0)' % (self.name,
				self.basetype, self.name)
		elif hasattr(self.typo.rule, 'literal_representation'):
			return self.typo.rule.literal_representation
		elif self.fromctbl:
			return self.name
		elif self.auxptr and not pref and typedesc[-1:] == '*':
			#  Would not hurt to have a pointer count in
			#  the parameter caller, where the logic would
			#  be "if param.ptrcount == self.ptrcount + 1"
			return 'p' + self.name
		else:
			name = self.name
			if field:
				if self.ptrcount:
					name = '%s->%s' % (name, field)
				else:
					name = '%s.%s' % (name, field)
			return pref + name
	def ptr(self):
		if self.ptrcount or self.dim:
			return self.name
		else:
			return '&' + self.name
	def rwptr(self):
		#
		#  Object for argument table, to be written by
		#  Python to C converter.  Caller will supply
		#  ampersand.  The auxiliary pointer allows an
		#  an object to get a null (pointer) value.
		#
		if self.auxptr:
			return 'p' + self.name
		else:
			return self.name
	def setup_p2c(self, full):
		self.typo.setup_p2c(full)
	def val(self):
		if self.ptrcount:
			return '*' + self.name
		else:
			return self.name
	def __repr__(self):
		name = getattr(self, 'name', None)
		cl = self.__class__.__name__
		r = '%s %s' % (self.type, name)
		return '<%s %s>' % (cl, repr(r))
	def __str__(self):
		x = getattr(self, 'name')
		if x is None:
			x = '(no name yet)'
		return x

#
#  Parameters are references to a variable, in a function argument list
#  but also returns, etc.  Parameters have type and position, and some
#  other attributes as required.  A parameter will eventually be attached
#  to a variable, and represents an application of that variable.
#
class Parameter:
	def __init__(self, type, passpref, pos, field, init, dim, ref):
		self.type = type
		self.passpref = passpref
		try:
			self.pos = int(pos)
		except ValueError:
			raise UnsupportedError, '(parameter name %s)' % (pos,)
		self.field = field
		if init:
			self.makeinitval(init)
		else:
			self.initval = None
		self.dim = dim
		self.refsem = ref
	def allocate(self, xf):
		if hasattr(self.dim, 'var'):
			return self.var.allocate(xf, self.dim.var)
		else:
			return self.var.allocate(xf, self.dim)
	def c2p(self, p):
		#
		#  Convert variable to a Python object.
		#  Parameter dimension here would be the result length
		#  of a buffer string, for example, as returned by
		#  a C++ function like File::Read().
		#
		if hasattr(self.dim, 'var'):
			dim = self.dim.var
		else:
			dim = self.dim
		return self.var.c2p(p, dim)
	def classify(self, var):
		var.classify()
		if self.passpref == '&':
			var.ampersand()
		return var
	def makeinitval(self, val):
		self.initval = Literal(val)
	def initptr(self):
		if self.initval:
			return '&' + self.initval.name
		else:
			return '0'
	def passout(self):
		return self.var.passout(self.type, self.passpref, self.refsem, self.field)
	def refsemantics(self):
		return self.refsem
	def setrefsemantics(self, name):
		self.refsem = name
	def setup_p2c(self):
		self.var.setup_p2c(0)
	def __repr__(self):
		var = getattr(self, 'var', None)
		vr = '(%s)' % repr(var)
		return '<%s %s@%s %s>' % (self.__class__.__name__, self.type, self.pos, vr)

#
#  Input is a special case of Parameter, an argument to the Python
#  API function.
#
class Input(Parameter):
	statics = ModuleStatics()

	def makeinitval(self, val):
		dtype = self.type
		if self.passpref == '&':
			dtype = dtype + '*'
		self.initval = self.statics.mkvalue(dtype, val)
	def setup_p2c(self):
		self.var.setup_p2c(1)

#
#  Parameters required for a Python API function and its one or more
#  C++ API overload functions.
#
class ParamTable:
	def __init__(self):
		self.tbl = []
	def dump(self):
		pl = []
		for pt in self.tbl:
			for v in pt.values():
				pl.append(v)
		return pl
	def index(self, type, pos):
		try:
			return self.tbl[pos][type]
		except (IndexError, KeyError):
			return None
	def set(self, type, pos, val):
		while pos >= len(self.tbl):
			self.tbl.append({})
		self.tbl[pos][type] = val

#
#  Positional parameter parser for a single function overload.
#
class ParamParser:
	psep = re.compile('[@%=]')

	def __init__(self):
		self.plist = []
	def parse(self, desc, table = None, vprefix = None):
		param, vp = self.parsedx(desc)
		self.resolve(param, vp, table, vprefix)
		return param
	#
	#  Parse a .dx parameter specification.
	#  Result is two variables, a parameter and its variable.
	#
	def parsedx(self, desc):
		s = self.psep.split(desc, 1)
		if len(s) == 2:
			if desc[len(s[0])] == '@':
				paramclass = Input
			else:
				paramclass = Parameter
			typedesc, pos = s
		else:
			raise ValueError, desc
		if typedesc[:1] == '&':
			passpref = '&'
			typedesc =  typedesc[1:]
		elif typedesc[:1] == '*':
			passpref = '*'
			typedesc =  typedesc[1:]
		else:
			passpref = ''

		var = Variable(typedesc)

		#  BMessage*@4!dup
		s = pos.split('!')
		if len(s) > 1:
			pos, s = s
			ref = s
		else:
			ref = None

		# int32@1=0
		s = pos.split('=')
		if len(s) > 1:
			pos, init = s
		else:
			init = None

		# string@1.ptr
		s = pos.split('.')
		if len(s) > 1:
			pos, field = s
		else:
			field = None

		#  Dimensions.
		pdim = None
		s = pos.split('[')
		if len(s) > 1:
			pos, dp = s
			sep = self.psep.search(dp)
			if sep:
				#  char*%3[@2
				#
				pdim = self.parse('int' + dp)
			else:
				if dp[:1] == '<':
					#  void*%0[<cobj->BitsLength() ...
					#
					pdim = Literal(dp[1:])
				else:
					#  A static dimension for the variable.
					var.dim = Literal(dp)

		param = paramclass(typedesc, passpref, pos, field, init, pdim, ref)
		return param, var
	def resolve(self, param, vp, table, vprefix):
		#
		#  Locate that variable.
		#
		pos = param.pos
		while len(self.plist) <= pos:
			self.plist.append(None)
		if table:
			#  Parameter resolution by type and position.
			#  This allows a function to share variables
			#  across several overloaded parameter lists.
			#  Normal parameters are resolved this way.
			#
			var = table.index(param.type, pos)
			if not var:
				var = vp
				param.classify(var)
				var.name = '%c%d' % (vprefix, pos)
				table.set(param.type, pos, var)
			param.var = var

			#  Rescue unresolved parameter references (dimensions)
			#  (see below)
			pv = self.plist[pos]
			if pv and not hasattr(pv, 'var'):
				pv.var = var
			self.plist[pos] = param
		else:
			#  Parameter resolution by position, specifically
			#  for parameter dimensions which are themselves
			#  parameters.  Specific to the present function
			#  overload, typeless.
			#
			pv = self.plist[pos]
			if pv:
				if hasattr(pv, 'var'):
					param.var = pv.var
				else:
					#  Two dimensions derived from the same
					#  parameter?  I guess it's possible!
					#  New one must die, first one wins.
					#
					param = pv
			else:
				self.plist[pos] = param
		return param
