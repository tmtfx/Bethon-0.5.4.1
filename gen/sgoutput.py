#  Copyright 1999 by Donn Cave, Seattle, Washington, USA.
#  All rights reserved.  Permission to copy, modify and distribute this
#  material is hereby granted, without fee, provided that the above
#  copyright notice appear in all copies.

from sgcf import cf

class CodeFile:
	def __init__(self, fp):
		self.fp = fp
		self.tab = 0
	def iput(self, s):
		self.put('	' * self.tab)
		self.put(s)
	def indent(self, x):
		self.tab = self.tab + x
		if self.tab < 0:
			self.tab = 0
	def put(self, s):
		self.fp.write(s)

class CFile:
	def __init__(self):
		self.file = None
		self.incl = {}
		self.bmpo = {}
		self.setabort()
	def append(self, st):
		self.file.iput(st + '\n')
	def code(self, st):
		self.file.iput(st + '\n')
	def abortif(self, t):
		self.file.iput('if (%s)\n' % t)
		self.file.indent(1)
		self.file.iput(self.abortexpr)
		self.file.indent(-1)
	def indent(self, d):
		self.file.indent(d)
	def iput(self, s):
		self.file.iput(s)
	def put(self, s):
		self.file.put(s)
	def setfile(self, file):
		r = self.file
		self.file = file
		return r
	def include(self, st):
		self.incl[st] = 1
	def includes(self):
		s = self.incl.keys()
		s.sort()
		return s
	def bmport(self, st):
		self.bmpo[st] = 1
	def bmports(self):
		s = self.bmpo.keys()
		s.sort()
		return s
	def setabort(self, expr=None):
		if expr:
			self.abortexpr = expr
		else:
			self.abortexpr = 'return 0;\n'


cf.files.xfuns = CodeFile(open('xxfuns.m4', 'w'))
cf.files.xgfun = CodeFile(open('xxgfun.m4', 'w'))
cf.files.xdefs = CodeFile(open('xxdefs.m4', 'w'))
cf.files.xdefs.iput('divert(-1)\n')
cf.files.xattr = CodeFile(open('xxattr.m4', 'w'))
cf.files.xincl = CodeFile(open('xxincl.m4', 'w'))
cf.files.xcode = CodeFile(open('xxcode.m4', 'w'))
cf.files.xglme = CodeFile(open('xxglme.m4', 'w'))
cf.files.xglsm = CodeFile(open('xxglsm.m4', 'w'))
cf.cfile = CFile()
