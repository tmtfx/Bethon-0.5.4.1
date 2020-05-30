#  Copyright 1999 by Donn Cave, Seattle, Washington, USA.
#  All rights reserved.  Permission to copy, modify and distribute this
#  material is hereby granted, without fee, provided that the above
#  copyright notice appear in all copies.

#  Generate C Python module code from class and rules descriptions.
#  The result is used in conjunction with an m4 module template
#  that lays out some standard module boilerplate.
#  - write out module definitions like name, symbols, base
#    classes, functions etc.  ... XXdefs.m4
#  - write out functions  XXfunctions.m4
#  - XXdefs.m4 includes module.m4
#  - module.m4 includes XXfunctions.m4

import re
import string
import sys

from sgcf import cf

#
#  Base class for parse node with non-leaf branches.  Any relation to
#  classic parse trees is accidental, here we have simply a topic like
#  "function" that has subtopics like "param".
#
#  "parse" method is invoked with split input line.  Class must provide
#  a function for interpreting this line, indexed by the first word in
#  the line.  E.g., to parse a nested input  '    take this for example':
#  in __init__, self.terms = {..., 'take':TakeOne, ...}
#  If the object returned by parse has its own "parse" function, it jumps
#  on top of the parse stack.
#
#  Subtopics like "define", which accepts nested input but where that
#  input is any old data, can provide a trivial definition of "parse",
#  returning None, themselves rather than inherit from this class.
#

class ClassElement:
	may_implement = 1
class Super:
	def attach(self, ob):
		self.elements.append(ob)
	def close(self):
		pass
	def generate(self):
		for el in self.elements:
			if hasattr(el, 'generate'):
				el.generate()
	def parse(self, file, args):
		term = self.terms[args[0]]
		x = term(args[1:])
		if hasattr(x, 'setfile'):
			x.setfile(file)
		self.attach(x)
		# print 'parse?', repr(x),
		if hasattr(x, 'parse'):
			# print 'has parse'
			return x
		else:
			# print 'has no parse'
			return None

class LineData:
	def __init__(self, args):
		self.data = []
		self.args = args
		if args:
			self.name = args[0]
	def parse(self, file, args):
		self.data.append(tuple(args))
		return None
	def __repr__(self):
		return '<%s %s: %s>' % (self.__class__.__name__, repr(self.args), repr(self.data))

class WordData(LineData):
	def parse(self, file, args):
		self.data = self.data + args
		return None

class Simple:
	def __init__(self, name, args):
		self.name = name
		self.args = args
	def __repr__(self):
		return '<%s %s>' % (self.name, self.args)

class ArgGen:
	def __init__(self, name):
		self.name = name
	def __call__(self, args):
		return Simple(self.name, args)
	def __repr__(self):
		return '<%s: %s>' % (self.__class__.__name__, self.name)

class SetArgs:
	def __init__(self, name):
		self.args = None
		self.name = name
	def __call__(self, args):
		self.args = tuple(args)
		return None
	def __repr__(self):
		return '<%s: %s>' % (self.__class__.__name__, repr(self.args))

class CommArgGen(ArgGen):
	def __call__(self, args):
		if args:
			# self.args = tuple(string.split(args[0], ','))
			a = string.split(string.join(args), ',')
			a.insert(0, self.name)
			return tuple(a)
		else:
			# self.args = ()
			return (self.name,)
		# return Simple(self.name, self.args)

class BlockArgGen(ArgGen):
	def __init__(self, args):
		ArgGen.__init__(self, args)
	def __call__(self, args):
		return CodeLines([self.name] + args)

class CodeLines(LineData):
	Range = 5
	def __getitem__(self, i):
		if i == 0:
			return self.name
		else:
			raise IndexError, i
	def __len__(self):
		return len(self.data) + 1
	def __getslice__(self, i, j):
		print 'getslice', i, j
		return self.data[i+1:j+1]
	def __getattr__(self, a):
		if a == 'index':
			return string.atoi(self.args[1])
		else:
			raise AttributeError, a

#  This could be general to derived classes, so class A's bases are
#  implicitly acquired through class B's explicit relationship to C.
#  But building any class would then require the whole suite of inherited
#  class definitions.  This way, that's only true among virtual-function
#  classes.
#
def getBaseVirtuals(base, baselist, methods, vfuns, vfndecl):
	baseparse = Parse()
	try:
		#  Location of .dx files could be handled better.
		baseparse.parseFile('%s/B%s.dx' % (cf.srcdir, base))
	except IOError, ev:
		print ev
	print 'base virtuals for', base
	for x in baseparse.nodelist:
		if x.__class__ != Top:
			continue
		for y in x.elements:
			if y.__class__ != Classe:
				continue
			for z in y.elements:
				if z.__class__ is Hook:
					z.may_call_base = 1
					z.generate()
					vfuns.append(z.name)
					vfndecl.append(z.decl())
				elif z.__class__ is Virtual:
					#  Pick up only new methods
					for m in methods:
						if m == z.name:
							print >> sys.stderr, 'duplicate', z.name, 'in', base
							# Probably OK to allow derived classes
							# override, in which case uncomment break.

							break
					else:
						z.may_implement = 1  # (pro forma)
						z.generate()
						methods.append(z.name)
			#  Make this pass last, so subclass methods prevail
			#  in Virtual clause above.
			for z in y.elements:
				if z.__class__ == Bases:
					#  Put immediate parents first, to please python 2.3
					#  else importing BButton fails because of different
					#  baseclass order than BControl...
					for name in z.name:
						baselist.append(name)
					for name in z.name:
						getBaseVirtuals(name, baselist, methods, vfuns, vfndecl)

class Classe(Super):
	def __init__(self, args):
		self.name = args[0]
		if len(args) > 1:
			self.fromself = args[1]
		else:
			self.fromself = 'var'
		self.elements = []
		self.terms = {'virtual':Virtual, 'hook':Hook, 'constructor':Constructor, 'attr':DataMember,
			'function':MemberFunction, 'preset':Preset, 'base':Bases}
	def close(self):
		pass
	def generate(self):
		cf.gen.classgen(self.name)
		bases = []
		methods = []
		attribs = []
		ctors = []
		preset = []
		vfuns = []
		vfndecl = []
		for el in self.elements:
			if not el.may_implement:
				continue
			try:
				el.generate()
			except cf.gen.UnsupportedError, val:
				try:
					nm = el.name
				except AttributeError:
					nm = repr(el)
				print nm, 'failed, unsupported', val
				el = None
			if not el:
				pass
			elif el.__class__ is Constructor:
				ctors = el.decl()
			elif el.__class__ is Hook:
				vfuns.append(el.name)
				vfndecl.append(el.decl())
			elif el.__class__ is MemberFunction or el.__class__ is Virtual:
				methods.append(el.name)
			elif el.__class__ is DataMember:
				attribs.append(el.name)
			elif el.__class__ is Preset:
				preset.append(el.name)
			elif el.__class__ is Bases:
				bases = bases + el.name

		baselist = bases[:]
		for base in bases:
			getBaseVirtuals(base, baselist, methods, vfuns, vfndecl)
		bases = baselist

		cf.gen.classlistgen(self.fromself, bases, methods, attribs, ctors, vfuns, vfndecl, preset)
	def __repr__(self):
		return '<class %s: %s>' % (self.name, repr(self.elements))

class Define(WordData):
	def generate(self):
		cf.gen.symgen(self.data)
class Include(WordData):
	def generate(self):
		cf.gen.inclgen(self.data)
class ModuleCode(LineData):
	def generate(self):
		cf.gen.codegen(self.data)

#  Function default options semantics:
#  on "input" statement recurrence, a new overload of the function appears.
#
class Function(Super):
	overloadkey = 'input'
	woverload = 'param'
	stdterms = ('input', 'param', 'status', 'return', 'byhand')
	def __init__(self, args):
		self.name = args[0]
		self.cname = self.name
		self.options(args[1:])
		self.terms = {}
		self.ostack = {}
		for i in self.stdterms:
			self.terms[i] = CommArgGen(i)
			self.ostack[i] = [None]
		self.terms['code'] = BlockArgGen('code')
		self.ostack['code'] = [None]
		self.ofun = ()
		self.over = 0
		self.file = '?'
	def options(self, opts):
		if opts:
			self.cname = opts[0]
	def setfile(self, file):
		self.file = file
	def close(self):
		pass
	def overload(self):
		for k in self.terms.keys():
			self.ostack[k].append(())
		self.over = self.over + 1
	def resolve(self):
		self.over = self.over + 1
		self.ofun = ('hi',)
		#  Propagate specs forward as defaults.
		#  print 'resolve', self.name, self.ostack
		for pl in self.ostack.values():
			defp = pl[0]
			for i in range(len(pl)):
				if pl[i]:
					defp = pl[i]
				else:
					pl[i] = defp
	def attach(self, ob):
		termname = ob[0]
		a = self.ostack[termname]
		if termname == self.overloadkey:
			if not a[self.over] is None:
				self.overload()
			# "param" initially defaults to same as "input"
			if self.woverload:
				self.ostack[self.woverload][self.over] = ob[1:]
		if type(ob) == type(()):
			a[self.over] = ob[1:]
		else:
			x = a[self.over]
			if not x:
				x = [None]*ob.Range
			x[ob.index] = ob.data
			a[self.over] = x
	def generate(self):
		if not self.ofun:
			self.resolve()
		cf.gen.fungen(self.name, self.cname, self.ostack, self.file)

class StaticMethod(Function):
	def generate(self):
		if not self.ofun:
			self.resolve()
		cf.gen.smgen(self.name, self.cname, self.ostack, self.file)

class MemberFunction(Function, ClassElement):
	def generate(self):
		if not self.ofun:
			self.resolve()
		cf.gen.methgen(self.name, self.cname, self.ostack, self.file)

class Constructor(MemberFunction):
	overloadkey = 'param'
	woverload = None
	def __init__(self, args):
		MemberFunction.__init__(self, [None])
	def decl(self):
		if not self.ofun:
			self.resolve()
		return cf.gen.ctor(self.ostack)
	def generate(self):
		pass

class Hook(MemberFunction):
	overloadkey = 'input'
	woverload = 'param'
	stdterms = ('input', 'param', 'status', 'return', 'byhand', 'loophandler')
	may_call_base = 1
	def options(self, opts):
		for opt in opts:
			if opt == 'none' or opt == 'None':
				self.may_call_base = 0
	def generate(self):
		if not self.ofun:
			self.resolve()
		cf.gen.hookgen(self.name, self.may_call_base, self.ostack, self.file)
	def decl(self):
		if not self.ofun:
			self.resolve()
		return cf.gen.hookdecl(self.name, self.ostack)

class Virtual(MemberFunction):
	def options(self, opts):
		self.cname = None
		for opt in opts:
			if opt == 'none' or opt == 'None':
				self.may_implement = None
			else:
				self.cname = opt
		if self.cname is None:
			self.cname = 'B`\'CLASS::' + self.name

class DataMember(Super, ClassElement):
	def __init__(self, args):
		self.name = args[0];
		self.elements = []
		self.terms = {'return':CommArgGen('return')}
	def generate(self):
		cf.gen.datagen(self.name, self.elements)

class Preset(ClassElement):
	def __init__(self, args):
		if len(args) > 1:
			v = args[1]
		else:
			v = args[0]
		self.name = '%s, %s' % (args[0], v)
	def generate(self):
		pass
class Bases(ClassElement):
	def __init__(self, args):
		self.name = args
	def generate(self):
		pass

class Top(Super):
	def __init__(self, file, args):
		self.terms = {'class':Classe, 'define':Define, 'include':Include, 'code':ModuleCode, 'function':Function, 'staticmethod':StaticMethod}
		self.file = file
		self.elements = []
	def attach(self, ob):
		self.elements.append(ob)
	def __repr__(self):
		return '<%s: %s>' % (self.__class__.__name__, repr(self.elements))

class Parse:
	def __init__(self):
		self.nodelist = []
	def parseFile(self, file):
		fp = open(file, 'r')
		stack = [Top(file, [])]
		level = 0
		while 1:
			x = fp.readline()
			if not x:
				break
			for lev in range(len(x)):
				if x[lev] != '	':
					break
			a = string.split(x)
			for i in range(len(a)):
				if a[i][:1] == '#':
					a = a[:i]
					break
			if not a:
				continue
			while lev < level:
				del stack[level]
				level = level - 1
			e = stack[level].parse(file, a)
			if not e is None:
				stack.append(e)
				level = level + 1
		self.nodelist.append(stack[0])
	def Generate(self):
		for node in self.nodelist:
			if hasattr(node, 'generate'):
				node.generate()
			else:
				print node.__class__.__name__, 'no generate'
		cf.gen.finish()

cf.parse = Parse()
