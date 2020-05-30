#  Copyright 1999 by Donn Cave, Seattle, Washington, USA.
#  All rights reserved.  Permission to copy, modify and distribute this
#  material is hereby granted, without fee, provided that the above
#  copyright notice appear in all copies.

import re
import string

from sgcf import cf
from sgvar import ParamParser, ParamTable, Variable, UnsupportedError

class Issue:
	def __init__(self, out):
		self.out = out
	def __call__(self, cfile):
		if self.out:
			cfile.iput(self.out);

#  Function derived from a single "input" statement.
class Function:
	fail = Issue('return 0;\n')
	castself = Issue(None)
	def __init__(self, name, cname, ds, vprfx, table):
		self.ds = ds
		self.name = name
		self.cname = cname
		self.parser = ParamParser()

		self.clist = []
		self.plist = []
		self.rlist = []
		self.slist = []
		listdict = {'input': self.plist, 'param': self.clist,
			'return': self.rlist, 'status': self.slist}

		for ltype in ('input', 'param', 'return', 'status'):
			vd = ds[ltype]
			if not vd:
				continue
			xlist = listdict[ltype]
			for i in range(len(vd)):
				p = self.parser.parse(vd[i], table, vprfx)
				xlist.append(p)
		self.autoparam = ds['byhand'] is None
	def pparams(self):
		for p in self.plist:
			p.setup_p2c()
		return len(self.plist)
	def cparams(self):
		pass
	def rparams(self):
		pass
	def looperspec(self):
		#  How to get at the looper for the right thread.
		handler = self.ds['loophandler']
		if not handler:
			return 'Looper()'
		else:
			p = self.parser.parse(handler[0])
			return '%s->Looper()' % p.var.name
	def docargtbl(self, width):
		crep = []
		for i in range(width):
			if i < len(self.plist):
				p = self.plist[i]
				if p.initval:
					crep.append('%s=%s' % (p.var.rule.ptype, p.initval.value))
				else:
					crep.append(p.var.rule.ptype)
		cret = []
		for r in self.rlist:
			cret.append(r.var.rule.ptype)
		return crep, cret
	def declargtbl(self, width):
		cfile = cf.cfile
		cfile.iput('{')
		for i in range(width):
			if i:
				cfile.put(', ')
			if i >= len(self.plist):
				cfile.put('{0, 0, 0, 0, 0}');
			else:
				p = self.plist[i]
				init = p.initptr()
				vr = p.var.rwptr()
				# cfile.put('{&%s, %s, %s_rep, %s_p2c, sizeof(%s)}' % (vr, init, p.var.rule, p.var.rule, vr))
				cfile.put('{&%s, %s, 0, %s_p2c, sizeof(%s)}' % (vr, init, p.var.rule, vr))

		cfile.put('}')
	def parse(self, i):
		cfile = cf.cfile
		cfile.put('if (ParseTuple(args, inp[%d], %d)) {\n' % (i, len(self.plist)))
		cfile.indent(1)
		self.putfuncall()
		cfile.indent(-1)
	def scopefun(self):
		return self.cname
	def putfuncall(self):
		cfile = cf.cfile
		ccode = self.ds['code']
		if ccode is None:
			ccode = ()
		# cfile.iput('// --- code slot 1 ---\n')
		if ccode and ccode[1]:
			for line in ccode[1]:
				cfile.iput(string.join(line) + '\n')
		for c in self.clist:
			allocs = c.allocate(cfile)
			for alloc in allocs:
				cfile.iput('if (!%s)\n' % alloc)
				cfile.indent(1)
				cfile.iput('return PyErr_NoMemory();\n')
				cfile.indent(-1)
		# cfile.iput('// --- code slot 2 ---\n')
		if ccode and ccode[2]:
			for line in ccode[2]:
				cfile.iput(string.join(line) + '\n')
		if self.slist and self.slist[0].pos == 0:
			fv = self.slist[0].var
		elif self.rlist and self.rlist[0].pos == 0:
			fv = self.rlist[0].var
		else:
			fv = None
		cfile.iput('Py_BEGIN_ALLOW_THREADS\n')
		if fv:
			cfile.iput('%s = ' % fv.name)
		else:
			cfile.iput('')
		cfile.put('%s(' % self.scopefun())
		cl = []
		for c in self.clist:
			cl.append(c.passout())
		cfile.put(string.join(cl, ', '))
		cfile.put(');\n')
		cfile.iput('Py_END_ALLOW_THREADS\n')
		if self.slist:
			cfile.iput('if (%s < B_OK)\n' % self.slist[0].var.name)
			cfile.indent(1)
			cfile.iput('return StatusError("%s", %s);\n' % (self.name, self.slist[0].var.name))
			cfile.indent(-1)
		for c in self.clist:
			if c.refsemantics() == 'incref':
				cfile.iput('Py_INCREF(PyTuple_GetItem(args, %d));\n' % (c.pos - 1))
		pyolist = []
		cprlist = []
		# cfile.iput('// --- code slot 3 ---\n')
		if ccode and ccode[3]:
			for line in ccode[3]:
				cfile.iput(string.join(line) + '\n')
		for r in self.rlist:
			n = 'P' + r.var.name
			pyolist.append(n)
			cprlist.append((r, n))
		if self.rlist:
			cfile.iput('PyObject *')
			cfile.put(string.join(pyolist, ', *'))
			cfile.put(';\n')
		for r, n in cprlist:
			p = Variable('PyObject*', n)
			if r.initval:
				cfile.iput('if (%s) {\n' % r.var)
				cfile.indent(1)
			r.c2p(p)
			if r.initval:
				cfile.indent(-1)
				cfile.iput('} else {\n')
				cfile.indent(1)
				x = str(r.initval)
				if x == 'None' or x == 'Py_None':
					cfile.iput('Py_INCREF(Py_None);\n');
					cfile.iput('%s = Py_None;\n' % (n,))
				else:
					cfile.iput('%s = %s;\n' % (n, x))
				cfile.indent(-1)
				cfile.iput('}\n')
		cfile.iput('PyObject *retv;\n')
		if len(self.rlist) == 0:
			cfile.iput('Py_INCREF(Py_None);\n')
			cfile.iput('retv = Py_None;\n')
		elif len(self.rlist) == 1:
			cfile.iput('retv = %s;\n' % pyolist[0])
		else:
			# cfile.iput('retv = Py_BuildValue("%s", ' % ('O' * len(self.rlist)))
			# cfile.put(string.join(pyolist, ', '))
			# cfile.put(');\n')
			cfile.iput('retv = PyTuple_New(%d);\n' % len(pyolist));
			i = 0
			for pyo in pyolist:
				cfile.iput('PyTuple_SetItem(retv, %d, %s);\n' % (i, pyo))
				i = i + 1
		for c in self.clist:
			c.var.free(cfile)
		# cfile.iput('// --- code slot 4 ---\n')
		if ccode and ccode[4]:
			for line in ccode[4]:
				cfile.iput(string.join(line) + '\n')
		cfile.iput('return retv;\n')

class MemberFunction(Function):
	def scopefun(self):
		return 'cobj->%s' % self.cname

class Constructor(MemberFunction):
	fail = Issue('return -1;\n')
	castself = Issue('PCLASS *self = (PCLASS *) selfob;\n')
	def putfuncall(self):
		ccode = self.ds['code']
		if ccode is None:
			ccode = ()
		#  "return" object is known in principle, and the m4 macros
		#  are more useful here than the description file return stmt.
		#
		# fv = self.rlist[0].cob.name
		cfile = cf.cfile
		cfile.iput("BCLASS *a0 = new BCLASS`'(")
		cfile.put(string.join(map(lambda v: v.passout(), self.clist), ', '))
		cfile.put(');\n')
		if self.slist:
			cfile.iput('if (%s != B_OK) {\n' % self.slist[0].var)
			cfile.indent(1)
			cfile.iput('StatusError("%s", %s);\n' % (self.name, self.slist[0].var))
			self.fail(cfile)
			cfile.indent(-1)
			cfile.iput('}\n')
		cfile.iput('if (!a0)\n')
		cfile.indent(1)
		self.fail(cfile)
		cfile.indent(-1)
		for c in self.clist:
			if c.refsemantics() == 'incref':
				cfile.iput('Py_INCREF(PyTuple_GetItem(args, %d));\n' % (c.pos - 1))
		cfile.iput('initBases();\n')
		# cfile.iput('// --- code slot 2 ---\n')
		if ccode and ccode[2]:
			for line in ccode[2]:
				cfile.iput(string.join(line) + '\n')
		# cfile.iput('// --- code slot 3 ---\n')
		if ccode and ccode[3]:
			for line in ccode[3]:
				cfile.iput(string.join(line) + '\n')
		cfile.iput('SETINT_BEPTR(self, a0);\n')
		cfile.iput('BINDINT_BEPTR(self, a0);\n')
		cfile.iput('ifdef(`VFUNS\', `a0->bindType(selfob);\')\n')
		# cfile.iput('// --- code slot 4 ---\n')
		if ccode and ccode[4]:
			for line in ccode[4]:
				cfile.iput(string.join(line) + '\n')
		cfile.iput('return 0;\n')

class VFunction(MemberFunction):
	def pparams(self):
		pass
	def rparams(self):
		for p in self.rlist:
			p.setup_p2c()

#  The set of the function's overloads.
class FunctionSet:
	def __init__(self, name, cname, ostack, fclass, cfname):
		self.name = name
		self.fclass = fclass
		self.cfname = cfname
		self.partbl = ParamTable()
		self.fs = []
		self.maxinpars = 0

		#  Invert overload stack to make a list of dicts of lists,
		#  from a dict of lists of lists.
		il = ostack.items()
		inv = []
		for i in range(len(il[0][1])):
			inv.append({})
			for k, v in il:
				inv[i][k] = v[i]
		vprfx = 'A'
		for o in inv:
			#
			#  Here is the parameter analysis.
			#
			self.fs.append(fclass(self.name, cname, o, vprfx, self.partbl))
			vprfx = chr(ord(vprfx) + 1)
		for o in self.fs:
			n = o.pparams()
			if self.maxinpars < n:
				self.maxinpars = n
		for o in self.fs:
			o.cparams()
		for o in self.fs:
			o.rparams()

	def declvars(self):
		for p in self.partbl.dump():
			for d in p.declare():
				cf.cfile.iput(d + ';\n')
	def docargtbl(self):
		frep = []
		for f in self.fs:
			crep, cret = f.docargtbl(self.maxinpars)
			frep.append(string.join(crep, ','))
		if cret:
			if len(cret) > 1:
				cret = '(%s)' % string.join(cret, ',')
			else:
				cret = cret[0]
			name = '%s %s' % (cret, self.name)
		else:
			name = self.name
		return 'static const char %s_doc[] = "%s(%s)";\n' % (self.cfname, name, string.join(frep, '|'))
	def declargtbl(self):
		cfile = cf.cfile
		if self.maxinpars > 0:
			#  Lay out table of argument overloads.
			#  Specify variable address, result variable address,
			#  default value and converter function for each.
			cfile.iput('struct InputParam inp[%d][%d] = {\n' % (len(self.fs), self.maxinpars))
			cfile.indent(1)
			lf = self.fs[-1]
			for f in self.fs:
				f.declargtbl(self.maxinpars)
				if not f is lf:
					cfile.put(',')
				cfile.put('\n')
			cfile.indent(-1)
			cfile.iput('};\n')

	def process(self):
		cfile = cf.cfile
		if self.maxinpars == 0:
			cfile.iput('if (PyTuple_Size(args)) {\n')
			cfile.indent(1)
			cfile.iput('PyErr_SetString(PyExc_TypeError, %s_doc);\n' % self.cfname)
			self.fclass.fail(cfile)
			cfile.indent(-1)
			cfile.iput('}\n');
			self.fs[0].putfuncall()
		elif not self.fs:
			cfile.iput('/* XXX no function parameter list specified! */\n')
		else:
			for i in range(len(self.fs)):
				if i == 0:
					cfile.iput('')
				else:
					cfile.iput('} else ')
				self.fs[i].parse(i)
			cfile.iput('} else {\n')
			cfile.indent(1)
			cfile.iput('PyErr_SetString(PyExc_TypeError, %s_doc);\n' % self.cfname)
			self.fclass.fail(cfile)
			cfile.indent(-1)
			cfile.iput('}\n');

class CC:
	def __init__(self):
		pass
	def codegen(self, list):
		for line in list:
			line = string.join(line)
			i = 0
			while line[i:i+2] == '^I':
				i = i + 2
			line = '\t'*(i/2) + line[i:]
			cf.files.xcode.put(line)
	def inclgen(self, list):
		st = 'define(`BE_INCLUDES\', `' + string.join(list, ', ') + '\')\n'
		cf.files.xdefs.put(st)
		cf.files.xincl.put(st)
	def classgen(self, name):
		self.name = 'B' + name
		xdefs = cf.files.xdefs
		xdefs.put('define(`CLASS\', `' + name + '\')\n')
		xdefs.put('define(`UPPERCLASS\', `' + string.upper(name) + '\')\n')
		xdefs.put('include(defs.m4)\n')
	def classlistgen(self, fromself, bases, methods, attribs, ctors, vfuns, vfundecl, preset):
		xdefs = cf.files.xdefs
		methods = filter(lambda x, n=self.name: x != n, methods)
		xdefs.put('define(`FROMSELF\', `' + fromself + '\')\n')
		xdefs.put('define(`BASES\', `' + string.join(bases, ', ') + '\')\n')
		xdefs.put('define(`METHODS\', `' + string.join(methods, ', ') + '\')\n')
		xdefs.put('define(`ATTRIBUTES\', `' + string.join(attribs, ', ') + '\')\n')
		xdefs.put('define(`CTORDCL\', `' + string.join(ctors, ', ') + '\')\n')
		if vfuns:
			xdefs.put('define(`VFUNS\', `' + string.join(vfuns, ', ') + '\')\n')
		if vfundecl:
			xdefs.put('define(`VFNDCL\', `' + string.join(vfundecl, ', ') + '\')\n')
		if preset:
			xdefs.put('define(`PRESET\', `' + string.join(preset, ', ') + '\')\n')
	def finish(self):
		xdefs = cf.files.xdefs
		if not hasattr(self, 'name'):
			self.name = 'Bconsts'
			xdefs.put('include(defs.m4)\n')
		xdefs.put('define(`FUNCINCL\', `xxfuns.m4\')\n')
		xdefs.put('define(`GFUNCINCL\', `xxgfun.m4\')\n')
		xdefs.put('define(`GLMETHINCL\', `xxglme.m4\')\n')
		xdefs.put('define(`GLSMINCL\', `xxglsm.m4\')\n')
		xdefs.put('define(`ATTRINCL\', `xxattr.m4\')\n')
		xdefs.put('define(`CODEINCL\', `xxcode.m4\')\n')
		xdefs.put('define(`IMPORTS\', `' + string.join(cf.cfile.bmports(), ', ') + '\')\n')
		xdefs.put('divert(0)\n')
		xdefs.put('include(template)\n')

	def symgen(self, data):
		cf.files.xdefs.iput('define(`SYMBOLS\', `' + string.join(data, ', ') + '\')\n')

	def ctor(self, ostack):
		elist = []
		for pl in ostack['param']:
			pes = ''
			pbs = ''
			for p in pl:
				p = string.split(p, '@')
				if pes:
					pes = pes + ', '
				pes = pes + p[0] + ' P' + p[1]
				if pbs:
					pbs = pbs + ', '
				pbs = pbs + 'P' + p[1]
			elist.append('BCLASS`\'(' + pes + '): B`\'CLASS`\'(' + pbs + ') {}')
		return elist

	#  Module level function.  (watch_node, stop_watch.)
	def fungen(self, name, cname, ostack, sourcefile):
		fclass = Function
		xfuns = cf.files.xfuns
		cf.cfile.setfile(xfuns)
		cfname = 'PyB_' + str(name)
		fset = FunctionSet(name, cname, ostack, fclass, cfname)
		xfuns.put('// from %s\n' % sourcefile)
		xfuns.put(fset.docargtbl())
		xfuns.put('static PyObject *\n');
		xfuns.put(cfname)
		xfuns.put('(PyObject *module, PyObject *args)\n{\n')
		xfuns.put('/* ' + repr(ostack) + ' */\n')
		xfuns.indent(1)
		fset.declvars()
		fset.declargtbl()
		fset.process()
		xfuns.indent(-1)
		xfuns.put('}\n\n')
		xglme = cf.files.xglme
		xglme.put('\t{"%s", %s, 1},\n' % (name, cfname))

	def smgen(self, name, cname, ostack, sourcefile):
		self.fungen(name, cname, ostack, sourcefile)
		cfname = str(name)
		xglsm = cf.files.xglsm
		xglsm.indent(1)
		xglsm.iput('PyObject *mf = PyDict_GetItemString(module_dict, "%s");\n' % cfname)
		xglsm.iput('if (mf) {\n');
		xglsm.indent(1)
		xglsm.iput('PyObject *sm = PyStaticMethod_New(mf);\n');
		xglsm.iput('if (sm)\n')
		xglsm.indent(1)
		xglsm.iput('PyDict_SetItemString(APITYPE.tp_dict, "%s", sm);\n' % cfname);
		xglsm.indent(-2)
		xglsm.iput('}\n')

	def methgen(self, name, cname, ostack, sourcefile):
		if name == self.name:
			fclass = Constructor
			xfuns = cf.files.xgfun
			frtype = 'int'
			argst = '(PyObject *selfob, PyObject *args, PyObject *kwds)'
			co = None
			fname = 'init'
		else:
			fclass = MemberFunction
			xfuns = cf.files.xfuns
			frtype = 'PyObject *'
			argst = '(PCLASS *self, PyObject *args)'
			co = 'B`\'CLASS *cobj = nativePtr(self); if (!cobj) return 0;\n'
			fname = str(name)
		cf.cfile.setfile(xfuns)
		cfname = 'PyB`\'CLASS`\'_' + name
		fset = FunctionSet(name, cname, ostack, fclass, cfname)
		xfuns.put('// from %s\n' % sourcefile)
		xfuns.put(fset.docargtbl())
		xfuns.put('static %s\n' % frtype);
		xfuns.put('PyB`\'CLASS`\'_' + fname)
		xfuns.put('%s\n{\n' % argst)
		xfuns.put('/* ' + repr(ostack) + ' */\n')
		xfuns.indent(1)
		fclass.castself(xfuns)
		fset.declvars()
		fset.declargtbl()
		if co:
			xfuns.iput(co)
		# xfuns.iput('static const char me[] = "%s";\n' % name);
		fset.process()
		xfuns.indent(-1)
		xfuns.put('}\n\n')

	def hookdecl(self, name, ostack):
		#  If there is to be a return value for the C++ function,
		#  it must come from the Python function, so we would find
		#  it in the "return" key.
		ret = ostack['return'][0]
		if ret:
			for retval in ret:
				retval = string.split(retval, '%')
				if len(retval) > 1 and retval[1][:1] == '0':
					ret = retval[0]
					break
			else:
				ret = 'void'
		else:
			ret = 'void'
		p = ostack['param'][0]
		if p is None:
			p = ''
		else:
			p = string.join(map(lambda x, s='@': string.split(x,s)[0], p), ', ')
		return 'virtual %s %s(`%s\');' % (ret, name, p)
	def hookgen(self, name, may_call_base, ostack, sourcefile):
		cf.cfile.setfile(cf.files.xfuns)
		xfuns = cf.files.xfuns
		o = {}
		for k, v in ostack.items():
			o[k] = v[0]
		ccode = o['code']
		if ccode is None:
			ccode = ()
		fun = VFunction(name, name, o, 'V', ParamTable())
		fun.cparams()
		fun.pparams()
		fun.rparams()
		#  How to specify the Looper for this thread.  This is
		#  by default the Handler's Looper() function ... and then
		#  a module-level m4 macro keeps this from being expressed
		#  in the case of the Looper class itself.
		looper = fun.looperspec()
		if fun.rlist:
			ret = 'void'
			for r in fun.rlist:
				if hasattr(r, 'pos'):
					if r.pos == 0:
						ret = r.type
				else:
					print r, 'has no pos'
		else:
			ret = 'void'
		arglist = []
		for arg in fun.clist:
			arglist.append('%s %s' % (arg.type, arg.var.name))
		xfuns.put('// from %s\n' % sourcefile)
		xfuns.put('%s\n' % ret)
		xfuns.put('Bpy%s::%s(%s)\n{\n' % (self.name[1:], name, string.join(arglist, ', ')))
		xfuns.put('/* ' + repr(ostack) + ' */\n')
		xfuns.indent(1)
		xfuns.iput('PyObject *argv;\n')
		xfuns.iput('PyObject *res = 0;\n')
		for r in fun.rlist:
			if r.pos == 0:
				fv = r.var
				xfuns.iput('%s %s;\n' % (fv.type, fv.name))
				break
		else:
			fv = None
		arglist = []
		for arg in fun.clist:
			arglist.append(arg.var.name)
		if may_call_base:
			basecall = '%s::%s(%s);\n' % (self.name, name, string.join(arglist, ', '))
		else:
			basecall = '// No implementation for this function.\n'
		if fun.rlist:
			basecall = 'return ' + basecall
		xfuns.iput('PyObject *fun;\n')
		xfuns.iput('looperspec(BLooper *looper;)\n')
		xfuns.iput('fun = lookup(v%s);\n' % name)
		xfuns.iput('if (!fun)\n')
		xfuns.indent(1)
		xfuns.iput('goto nofun;\n')
		xfuns.indent(-1)
		xfuns.iput('looperspec(looper = %s;)\n' % looper);
		xfuns.iput('if (looperspec(!looper || )looperspec(looper->)Thread() < B_NO_ERROR || !getPyThread(looperspec(looper)))\n')
		xfuns.indent(1)
		xfuns.iput('goto nofun;\n')
		xfuns.indent(-1)
		xfuns.iput('if (PyErr_Occurred()) {\n')
		xfuns.indent(1)
		xfuns.iput('releasePyThread(looperspec(%s));\n' % looper)
		xfuns.iput('goto nofun;\n')
		xfuns.indent(-1)
		xfuns.iput('}\n')
		xfuns.iput('goto goodfun;\n')
		xfuns.iput('nofun:\n')
		xfuns.indent(1)
		xfuns.iput(basecall)
		if not fun.rlist:
			xfuns.iput('return;\n')
		xfuns.indent(-1)
		xfuns.iput('goodfun:\n')
		pyolist = []
		pprlist = []
		if fun.autoparam:
			for o in fun.plist:
				n = 'P' + o.var.name
				pyolist.append(n)
				pprlist.append((o, n))
			cf.cfile.setabort('goto abt;\n')
			if len(fun.plist) > 0:
				xfuns.iput('argv = PyTuple_New(%d);\n' % len(fun.plist))
				xfuns.iput('if (!argv)\n')
				xfuns.indent(1)
				xfuns.iput('goto abt;\n')
				xfuns.indent(-1)
			else:
				xfuns.iput('argv = 0;\n')
			if fun.plist:
				xfuns.iput('PyObject *')
				xfuns.put(string.join(pyolist, ', *'))
				xfuns.put(';\n')
			i = 0
			for o, n in pprlist:
				p = Variable('PyObject*', n)
				if o.var.ptrcount > 0:
					xfuns.iput('if (!%s) {\n' % o.var.name)
					xfuns.indent(1)
					xfuns.iput('%s = Py_None;\n' % n)
					xfuns.iput('Py_INCREF(Py_None);\n')
					xfuns.indent(-1)
					xfuns.iput('} else {\n')
					xfuns.indent(1)
				o.c2p(p)
				if o.var.ptrcount > 0:
					xfuns.indent(-1)
					xfuns.iput('}\n')
				xfuns.iput('PyTuple_SetItem(argv, %d, %s);\n' % (i, n))
				i = i + 1
			# if len(fun.clist) == 0:
			# 	xfuns.iput('argv = 0;\n')
			# else:
			# 	xfuns.iput('argv = Py_BuildValue("(%s)", %s);\n' % (('O' * len(fun.clist)), string.join(pyolist, ', ')))
		# xfuns.iput('// --- code slot 2 ---\n')
		if ccode and ccode[2]:
			for line in ccode[2]:
				xfuns.iput(string.join(line) + '\n')
		xfuns.iput('res = PyEval_CallObject(fun, argv);\n')
		xfuns.put('abt:\n')
		xfuns.iput('if (res) {\n')
		xfuns.indent(1)
		if len(fun.rlist) == 1:
			pv = Variable('PyObject*', 'res')
			r = fun.rlist[0]
			r.var.p2c(pv)
		elif len(fun.rlist) > 1:
			for i in range(len(fun.rlist)):
				pv = Variable('PyObject*', 'PyTuple_GetItem(res, %d)' % i)
				r = fun.rlist[i]
				r.var.p2c(pv)
		xfuns.iput('Py_DECREF(res);\n')
		xfuns.indent(-1)
		xfuns.iput('} else {\n')
		xfuns.indent(1)
		# xfuns.iput('PyErr_Print();\n')
		xfuns.iput('lastchance(looperspec(%s));\n' % looper)
		xfuns.indent(-1)
		xfuns.iput('}\n')
		xfuns.iput('if (argv)\n')
		xfuns.indent(1)
		xfuns.iput('Py_DECREF(argv);\n')
		xfuns.indent(-1)
		cf.cfile.setabort()
		xfuns.iput('releasePyThread(looperspec(%s));\n' % looper)
		xfuns.iput('if (res)\n')
		xfuns.indent(1)
		if fv:
			xfuns.iput('return %s;\n' % fv.name)
		else:
			xfuns.iput('return;\n')
		xfuns.indent(-1)
		xfuns.iput('else {\n')
		xfuns.indent(1)
		xfuns.iput('be_app->PostMessage(B_QUIT_REQUESTED);\n')
		if name == 'QuitRequested':
			xfuns.iput('return 1;\n')
		elif fv:
			#  Arbitrary maybe, but not random anyway.
			xfuns.iput('return 0;\n')
		# xfuns.iput('looperspec(`%s->\')Quit();\n' % looper)
		# xfuns.iput('be_app->Lock();\n');
		# xfuns.iput('be_app->Quit();\n');
		xfuns.indent(-1)
		xfuns.iput('}\n')
		xfuns.indent(-1)
		xfuns.put('}\n\n')

	def vfundecl(self, name, ostack):
		ret = ostack['return'][0]
		if ret:
			ret = string.split(ret[0], '%')[0]
		else:
			ret = 'void'
		p = ostack['param'][0]
		if p is None:
			p = ''
		else:
			p = string.join(map(lambda x, s='@': string.split(x,s)[0], p), ', ')
		return 'virtual %s %s(`%s\');' % (ret, name, p)

	def datagen(self, name, elements):
		xattr = cf.files.xattr
		cf.cfile.setfile(xattr)
		xattr.indent(1)
		xattr.iput('if (!strcmp(name, "%s")) {\n' % name)
		xattr.indent(1)
		xattr.iput('/* %s */\n' % string.join(elements[0]))
		ret = elements[0]
		xattr.iput('PyObject *ret;\n')
		v = Variable(ret[1], 'cobj->' + name)
		v.classify()
		r = Variable('PyObject*', 'ret')
		v.c2p(r)
		xattr.iput('return ret;\n')
		xattr.indent(-1)
		xattr.iput('}\n')
		xattr.indent(-1)

cf.gen = CC()
cf.gen.UnsupportedError = UnsupportedError
