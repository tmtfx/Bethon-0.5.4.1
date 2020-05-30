#  Copyright 1999 by Donn Cave, Seattle, Washington, USA.
#  All rights reserved.  Permission to copy, modify and distribute this
#  material is hereby granted, without fee, provided that the above
#  copyright notice appear in all copies.

import string
import sys

from sgcf import cf
from sgvar import Variable

class RuleBase:
	makepointer = 0
	storage = None
	def pretpgen(self):
		pass
	def __str__(self):
		name = getattr(self, 'name', None)
		if not name:
			name = self.__class__.__name__
		return name

#  get from/to functions from exported CObject
#
class CTbl:
	def __init__(self, name, rule):
		self.name = name
		self.rule = rule
	def require(self, forwhat = None):
		if hasattr(cf.gen, 'name') and cf.gen.name == self.name:
			#  This one is our own module.
			return 'cfunctions.'
		cf.cfile.bmport(self.name)
		tbl = self.name + 'CTbl'
		if forwhat:
			cf.cfile.abortif('!%s && !isBThing(%s)' % (tbl, forwhat))
		cf.cfile.iput('if (!%s)\n' % tbl)
		cf.cfile.indent(1)
		cf.cfile.iput('%s = (BaseFunctions *) PyCObject_Import("%s", "functions");\n' % (tbl, self.name))
		cf.cfile.indent(-1)
		cf.cfile.abortif('!' + tbl)
		return tbl + '->'

class CImporter(RuleBase):
	storage = Variable.CTBL
	ctbl = None
	pretpok = ['OK']
	def pretpgen(self):
		if self.pretpok:
			cf.cfile.put('//  Check for Bxx module, to save an import if parameter is a string or something\n')
			del self.pretpok[0]
			#  Nice m4 macro, instead of writing the vile hacks here
			cf.cfile.put('isB()\n')
	def p2c(self, inm, onm):
		if not self.ctbl:
			self.ctbl = CTbl(self.ptype, self)
		tbl = self.ctbl.require(inm.ptr())
		if onm.ptrcount > 0:
			cf.cfile.iput('%s = (%s) %sAsIt(%s);\n' % (onm.ptr(), onm.type, tbl, inm.ptr()))
			cf.cfile.abortif('!%s' % onm.ptr())
			# cf.cfile.iput('%s = (%s) %sAsIt(%s);\n' % (onm.ptr(), self.vtype, tbl, inm.ptr()))
		else:
			#  AsBFont returns pointer, but .font is value.
			cf.cfile.iput('%s = *((%s *) %sAsIt(%s));\n' % (onm.val(), onm.type, tbl, inm.ptr()))
	def c2p(self, inm, onm, dim):
		if not self.ctbl:
			self.ctbl = CTbl(self.ptype, self)
		tbl = self.ctbl.require()
		internal = inm.storage == inm.HEAP
		cf.cfile.iput('%s = %sFromIt(%s, %d);\n' % (onm.ptr(), tbl, inm.ptr(), internal))
		cf.cfile.abortif('!%s' % onm.ptr())

class Int32Rules(RuleBase):
	target = ('int32',
		'long',
		'alert_type',
		'alignment',
		'alpha_function',
		'app_verb',
		'bitmap_tiling',
		'border_style',
		'buffer_orientation',
		'buffer_layout',
		'button_spacing',
		'button_width',
		'cap_mode',
		'color_space',
		'color_which',
		'color_control_layout',
		'data_bits',
		'data_rate',
		'dev_t',
		'drawing_mode',
		'file_panel_button',
		'file_panel_mode',
		'font_direction',
		'font_file_format',
		'hash_mark_location',
		'icon_size',
		'join_mode',
		'list_view_type',
		'menu_bar_border',
		'menu_layout',
		'orientation',
		'parity_mode',
		'perform_code',
		'sem_id',
		'size_t',
		'source_alpha',
		'ssize_t',
		'status_t',
		'stop_bits',
		'team_id',
		'thread_id',
		'thumb_style',
		'time_t',
		'type_code',
		'version_kind',
		'vertical_alignment',
		'window_alignment',
		'window_type',
		'window_look',
		'window_feel'
	)
	name = 'tplong'
	vtype = 'long'
	ptype = 'int'
	bldval = 'l'
	def pck(self, inm):
		cf.cfile.iput('PyInt_Check(%s)' % inm.ptr())
	def p2c(self, inm, onm):
		cf.cfile.abortif('!PyInt_Check(%s)' % inm.ptr())
		cf.cfile.iput('%s = PyInt_AsLong(%s);\n' % (onm.val(), inm.ptr()))
	def c2p(self, inm, onm, dim):
		cf.cfile.iput('%s = PyInt_FromLong(%s);\n' % (onm.ptr(), inm.val()))
		cf.cfile.abortif('!%s' % onm.ptr())

class Int16Rules(Int32Rules):
	target = ('short', 'int16')
	name = 'tpshort'
	vtype = 'int16'  # Was "int"
	ptype = 'int'
	bldval = 'i'

class Int8Rules(Int32Rules):
	target = ('int8', 'bool')
	name = 'tpbyte'
	vtype = 'int8'
	ptype = 'int'
	bldval = 'c'

class Int64Rules(Int32Rules):
	target = ('int64', 'bigtime_t', 'off_t')
	name = 'tplonglong'
	vtype = 'int64'
	ptype = 'long'
	bldval = 'l'
	bldcast = 'long'
	def p2c(self, inm, onm):
		#  Hm, longs probably should be legit for all int types?
		cf.cfile.iput('if (PyLong_Check(%s))' % inm.ptr())
		cf.cfile.indent(1)
		cf.cfile.iput('%s = PyLong_AsLongLong(%s);\n' % (onm.val(), inm.ptr()))
		cf.cfile.indent(-1)
		cf.cfile.iput('else if (PyInt_Check(%s))\n' % inm.ptr())
		cf.cfile.indent(1)
		cf.cfile.iput('%s = PyInt_AsLong(%s);\n' % (onm.val(), inm.ptr()))
		cf.cfile.indent(-1)
		cf.cfile.iput('else\n')
		cf.cfile.indent(1)
		cf.cfile.iput(cf.cfile.abortexpr + '\n')
		cf.cfile.indent(-1)
	def c2p(self, inm, onm, dim):
		cf.cfile.iput('%s = PyLong_FromLongLong(%s);\n' % (onm.ptr(), inm.val()))
		cf.cfile.abortif('!%s' % onm.ptr())

class UInt8Rules(Int8Rules):
	target = ('uint8',)
	name = 'tpuint8'
	vtype = 'uint8'
	ptype = 'int'
	bldval = 'b'

class UInt16Rules(Int16Rules):
	target = ('uint16',)
	name = 'tpuint16'
	vtype = 'uint16'
	ptype = 'int'
	bldval = 'h'

class UInt32Rules(Int32Rules):
	target = ('uint32','uid_t','gid_t', 'mode_t')
	name = 'tpulong'
	vtype = 'unsigned long'
	ptype = 'int'
	bldval = 'l'
	def p2c(self, inm, onm):
		cf.cfile.iput('if (PyInt_Check(%s))\n' % inm.ptr())
		cf.cfile.indent(1)
		cf.cfile.iput('%s = PyInt_AsLong(%s);\n' % (onm.val(), inm.ptr()))
		cf.cfile.indent(-1)
		cf.cfile.iput('else if (PyLong_Check(%s))\n' % inm.ptr())
		cf.cfile.indent(1)
		cf.cfile.iput('%s = PyLong_AsLong(%s);\n' % (onm.val(), inm.ptr()))
		cf.cfile.indent(-1)
		cf.cfile.iput('else\n')
		cf.cfile.indent(1)
		cf.cfile.iput('return 0;\n')
		cf.cfile.indent(-1)
	def c2p(self, inm, onm, dim):
		# PyLong because it's the only Unsigned conversion I know of.
		cf.cfile.iput('%s = PyLong_FromUnsignedLong(%s);\n' % (onm.ptr(), inm.val()))
		cf.cfile.abortif('!%s' % onm.ptr())

class DoubleRules(RuleBase):
	target = ('double',)
	name = 'tpfloat'
	vtype = 'double'
	ptype = 'float'
	bldval = 'd'
	def pck(self, inm):
		cf.cfile.iput('PyFloat_Check(%s)' % inm.ptr())
	def p2c(self, inm, onm):
		cf.cfile.abortif('!PyFloat_Check(%s)' % inm.ptr())
		cf.cfile.iput('%s = PyFloat_AsDouble(%s);\n' % (onm.val(), inm.ptr()))
	def c2p(self, inm, onm, dim):
		cf.cfile.iput('%s = PyFloat_FromDouble(%s);\n' % (onm.ptr(), inm.val()))
		cf.cfile.abortif('!%s' % onm.ptr())

class FloatRules(DoubleRules):
	target = ('float',)
	name = 'tpfloat'
	vtype = 'float'
	ptype = 'float'
	bldval = 'f'
	bldcast = 'double'
	def pck(self, inm):
		cf.cfile.iput('PyFloat_Check(%s)' % inm.ptr())
	def p2c(self, inm, onm):
		cf.cfile.abortif('!PyFloat_Check(%s)' % inm.ptr())
		cf.cfile.iput('%s = PyFloat_AsDouble(%s);\n' % (onm.val(), inm.ptr()))
	def c2p(self, inm, onm, dim):
		cf.cfile.iput('%s = PyFloat_FromDouble(%s);\n' % (onm.ptr(), inm.val()))
		cf.cfile.abortif('!%s' % onm.ptr())

class IFloatRules(FloatRules):
	target = ('ifloat',)
	name = 'tpifloat'
	ptype = 'ifloat'
	def pck(self, inm):
		cf.cfile.iput('PyNumber_Check(%s)' % inm.ptr())
	def p2c(self, inm, onm):
		cf.cfile.abortif('!PyNumber_Check(%s)' % inm.ptr())
		cf.cfile.iput('%s = PyFloat_AsDouble(%s);\n' % (onm.val(), inm.ptr()))
class CharPtrRules(RuleBase):
	target = ('char','void', 'font_family', 'font_style')
	name = 'tpcharptr'
	vtype = 'char*'
	ptype = 'string'
	bldval = 's'
	def pck(self, inm):
		cf.cfile.iput('PyString_Check(%s)' % inm.ptr())
	def p2c(self, inm, onm):
		cf.cfile.iput('%s = PyString_AsString(%s);\n' % (onm.ptr(), inm.ptr()))
		cf.cfile.abortif('!%s' % onm.ptr())
		cf.cfile.iput('// hack alert:\n')
		cf.cfile.iput('if (p->size == 1) {\n')
		cf.cfile.iput('\t*((char *) p->var) = *%s;\n' % onm.ptr())
		cf.cfile.iput('\treturn 1;\n')
		cf.cfile.iput('}\n')
	def c2p(self, inm, onm, dim):
		if dim:
			cf.cfile.iput('%s = PyString_FromStringAndSize((char *) %s, %s);\n' % (onm.ptr(), inm.ptr(), dim))
		else:
			cf.cfile.iput('%s = PyString_FromString(%s);\n' % (onm.ptr(), inm.ptr()))
		cf.cfile.abortif('!%s' % onm.ptr())

class NullRules(RuleBase):
	target = ('None',)
	name = 'tpnull'
	vtype = 'None'
	ptype = 'None'
	structdef = 'typedef void *None;'
	bldval = 's'
	literal_representation = '0'
	def pck(self, inm):
		cf.cfile.iput('%s == Py_None' % inm.ptr())
	def p2c(self, inm, onm):
		cf.cfile.abortif('%s != Py_None' % inm.ptr())
		cf.cfile.iput('%s = 0;\n' % onm.val())
	def c2p(self, inm, onm, dim):
		cf.cfile.iput('%s = Py_None;\n' % (onm.ptr(),))

class patternRules(CharPtrRules):
	target = ('pattern',)
	name = 'tppattern'
	vtype = 'pattern'
	ptype = 'string'
	fixedlength = 8
	def pck(self, inm):
		cf.cfile.iput('PyString_Check(%s) && PyString_Size(%s) == %d' % (inm.ptr(), inm.ptr(), self.fixedlength))
	def p2c(self, inm, onm):
		cf.cfile.abortif('PyString_Size(%s) != %d' % (inm.ptr(), self.fixedlength))
		cf.cfile.iput('memcpy(%s.data, PyString_AsString(%s), %d);\n' % (onm.val(), inm.ptr(), self.fixedlength))
	def c2p(self, inm, onm, dim):
		cf.cfile.iput('%s = PyString_FromStringAndSize((char *) %s.data, %s);\n' % (onm.ptr(), inm.val(), self.fixedlength))
		cf.cfile.abortif('!%s' % onm.ptr())

class fixed8Rules(CharPtrRules):
	target = ()
	name = 'tpfixed8'
	vtype = 'char*'
	ptype = 'string'
	fixedlength = 8
	bldval = None
	def pck(self, inm):
		cf.cfile.iput('PyString_Check(%s) && PyString_Size(%s) == %d' % (inm.ptr(), inm.ptr(), self.fixedlength))
	def p2c(self, inm, onm):
		cf.cfile.abortif('PyString_Size(%s) != %d' % (inm.ptr(), self.fixedlength))
		cf.cfile.iput('memcpy(%s, PyString_AsString(%s), %d);\n' % (onm.ptr(), inm.ptr(), self.fixedlength))
	def c2p(self, inm, onm, dim):
		cf.cfile.iput('%s = PyString_FromStringAndSize((char *) %s, %s);\n' % (onm.ptr(), inm.ptr(), self.fixedlength))
		cf.cfile.abortif('!%s' % onm.ptr())

class char8Rules(CharPtrRules):
	target = ()
	name = 'tpchar8'
	vtype = 'char*'
	ptype = 'string'
	fixedlength = 8
	bldval = None
	def p2c(self, inm, onm):
		cf.cfile.iput('strncpy(%s, PyString_AsString(%s), %d);\n' % (onm.ptr(), inm.ptr(), self.fixedlength))
	def c2p(self, inm, onm, dim):
		cf.cfile.iput('{int clen = strlen(%s);\n' % inm.ptr())
		cf.cfile.iput(' if (clen >= %s)\n' % self.fixedlength)
		cf.cfile.iput('   clen = %s;\n' % (self.fixedlength - 1,))
		cf.cfile.iput('%s = PyString_FromStringAndSize((char *) %s, clen);\n' % (onm.ptr(), inm.ptr()))
		cf.cfile.iput('}\n')
		cf.cfile.abortif('!%s' % onm.ptr())

class char64Rules(char8Rules):
	name = 'tpchar64'
	fixedlength = 64
class char256Rules(char8Rules):
	name = 'tpchar256'
	fixedlength = 256

class StringRules(RuleBase):
	target = ('pstring',)
	name = 'tpstring'
	vtype = 'struct StringDx'
	structdef = 'typedef struct StringDx {\n\tchar *ptr;\n\tint len;\n} pstring;'
	ptype = 'string'
	bldval = '#s'
	def pck(self, inm):
		cf.cfile.iput('PyString_Check(%s)' % inm.ptr())
	def p2c(self, inm, onm):
		cf.cfile.iput('%s.ptr = PyString_AsString(%s);\n' % (onm.val(), inm.ptr()))
		cf.cfile.abortif('!%s' % onm.ptr())
		cf.cfile.iput('%s.len = PyString_Size(%s);\n' % (onm.val(), inm.ptr()))
	def c2p(self, inm, onm, dim):
		cf.cfile.iput('%s to %s kind of a surprise.\n' % (inm.ptr(), onm.ptr()))

class SeqRules(RuleBase):
	target = ()
	storage = Variable.HEAP
	def c2p(self, inm, onm, dim):
		cf.cfile.iput('%s = Py%s_New(%s);\n' % (onm.ptr(), self.seqtype, dim.val()))
		cf.cfile.abortif('!%s' % onm.ptr())
		cf.cfile.iput('int i;\n')
		cf.cfile.iput('for (i = 0; i < %s; ++i) {\n' % dim.val())
		cf.cfile.indent(1)
		ps = Variable('PyObject*', 'pelem')
		cf.cfile.iput('PyObject *pelem;\n')
		vs = Variable(self.vetype, 'celem')
		vs.classify(self.elementrule)
		#  Why inm.val()?
		cf.cfile.iput('%s celem = %s[i];\n' % (self.vetype, inm.val()))
		vs.c2p(ps)
		cf.cfile.iput('Py%s_SetItem(%s, i, %s);\n' % (self.seqtype, onm.ptr(), ps.ptr()))
		cf.cfile.indent(-1)
		cf.cfile.iput('}\n')
	def p2c(self, inm, onm):
		cf.cfile.iput('int i;\n')
		cf.cfile.iput('int n = Py%s_Size(%s);\n' % (self.seqtype, inm.ptr()))
		cf.cfile.iput('%s.ptr = (%s) malloc(%s);\n' % (onm.val(), self.vatype, self.allocsize('n')))
		cf.cfile.abortif('!%s.ptr' % onm.val())
		cf.cfile.iput('%s.len = n;\n' % onm.val())
		cf.cfile.iput('for (i = 0; i < n; ++i) {\n')
		cf.cfile.indent(1)
		ps = Variable('PyObject*', 'pelem')
		cf.cfile.iput('PyObject *pelem;\n')
		vs = Variable(self.vetype, 'celem')
		vs.classify(self.elementrule)
		cf.cfile.iput('pelem = Py%s_GetItem(%s, i);\n' % (self.seqtype, inm.ptr()))
		cf.cfile.iput('%s celem;\n' % self.vetype)
		vs.p2c(ps)
		#  XX Too easy, won't be good for fancy structs.
		cf.cfile.iput('%s.ptr[i] = celem;\n' % onm.val())
		cf.cfile.indent(-1)
		cf.cfile.iput('}\n')
		self.lastelem(onm, 'i')
	def lastelem(self, onm, e):
		pass

class ArgvpRules(SeqRules):
	target = ('argvp',)
	seqtype = 'Sequence'
	vtype = 'struct ArgvDx'
	name = 'tpargv'
	ptype = 'list'
	vatype = 'char**'
	vetype = 'char*'
	elementrule = CharPtrRules()
	def allocsize(self, count):
		# return 'sizeof(%s) * %s + sizeof(struct ArgvDx)' % (self.vetype, count)
		return 'sizeof(%s) * (%s + 1)' % (self.vetype, count)
	def pretpgen(self):
		cf.cfile.iput('typedef struct ArgvDx {\n\tint len;\n\tchar **ptr;\n} argvp;\n')
	def csize(self, inm, onm):
		cf.cfile.iput('for (%s = 0; %s[%s]; ++%s)\n' % (onm.val(), inm.ptr(), onm.val(), onm.val()))
		cf.cfile.iput('	;\n')
	def lastelem(self, onm, e):
		cf.cfile.iput('%s.ptr[%s] = 0;\n' % (onm.val(), e))

class ArgvcRules(SeqRules):
	target = ('argvc',)
	seqtype = 'Tuple'
	vtype = 'char**'
	ptype = 'tuple'
	name = 'tpargvc'
	vatype = 'char**'
	vetype = 'char*'
	elementrule = CharPtrRules()
	def allocsize(self, count):
		return 'blah'

class NVar:
	def __init__(self, expr):
		self.ptr_ = expr
		self.val_ = expr
	def ptr(self):
		return self.ptr_
	def val(self):
		return self.val_

#  Structs like stat, attr_info, etc. that don't warrant their own
#  C implementation.
#
class TupleBase(RuleBase):
	# Tuple base expects:
	# target: (type as in module description file, ...)
	# name: for p2c conversion function.
	# vtype: for declarations
	# ptype: for Python users
	# members = ((struct member, rule instance), ...)
	ptype = 'tuple'
	makepointer = 1
	bldval = None
	def p2c(self, inm, onm):
		cf.cfile.iput('if (PyTuple_Check(%s) && PyTuple_Size(%s) == %d) {\n' % (inm.ptr(), inm.ptr(), len(self.members)))
		cf.cfile.indent(1)
		i = 0
		for m, r in self.members:
			cf.cfile.iput('PyObject *p%s = PyTuple_GetItem(%s, %d);\n' % (m, inm.ptr(), i))
			i = i + 1
			pv = NVar('p' + m)
			if onm.ptrcount:
				mve = '%s->' % onm.ptr()
			else:
				mve = '%s.' % onm.val()
			mv = Variable(r.vtype, '%s%s' % (mve, m))
			r.p2c(pv, mv)
		cf.cfile.indent(-1)
		cf.cfile.iput('} else\n')
		cf.cfile.indent(1)
		cf.cfile.iput(cf.cfile.abortexpr + '\n')
		cf.cfile.indent(-1)
	def c2p(self, inm, onm, dim):
		bldval = ''
		mv = []
		pmx = 1
		for m, r in self.members:
			if inm.ptrcount > 0:
				inmprefix = '%s->' % inm.ptr()
			else:
				inmprefix = '%s.' % inm.val()
			nm = '%s%s' % (inmprefix, m)
			if r.bldval is None:
				b = 'O'
				cm = Variable(r.vtype, nm)
				cm.classify(r)
				pmn = 'PM%d' % pmx
				cf.cfile.iput('PyObject *%s;\n' % pmn)
				pm = Variable('PyObject*', pmn)
				pmx = pmx + 1
				cm.c2p(pm)
			else:
				b = r.bldval
			bldval = bldval + b
			#
			#  Casting:  avoid passing int16 to a stdarg(...)
			#  function that expects int32 - or whatever.
			#  This is tricky, and naturally I will resort
			#  to hackery.
			#
			if b == 'O':
				mv.append(pmn)
				# Should this be DECREF'd, after bldvalue?
			elif hasattr(r, 'bldcast'):
				mv.append('(%s) %s%s' % (r.bldcast, inmprefix, m))
			else:
				mv.append('%s%s' % (inmprefix, m))
		cf.cfile.iput('%s = Py_BuildValue("%s", %s);\n' % (onm.ptr(), bldval, string.join(mv, ', ')))
		cf.cfile.abortif('!%s' % onm.ptr())
	def classgen(self, fp):
		#  Generate class to name tuple items.
		#  Drop leading "struct", if any.
		name = string.split(self.vtype)[-1]
		fp.write('class %s(Structuple):\n' % name)
		ml = []
		tl = []
		for m, t in self.members:
			if hasattr(t, 'classgen'):
				t = string.split(t.vtype)[-1]
			else:
				t = 'None'
			tl.append(t)
			ml.append('\'%s\'' % m)
		fp.write('\t_members = (%s)\n' % string.join(ml, ', '))
		fp.write('\tdef typegen(self):\n')
		fp.write('\t\treturn (%s)\n' % string.join(tl, ', '))
		fp.write('\n')

#  Tuples representing serious classes whose constructors and destructors
#  need to be involved in things.
#
class CTorTuple(TupleBase):
	def p2c(self, inm, onm):
		mvlist = []
		for m, r in self.members:
			cf.cfile.iput('%s %s;\n' % (r.vtype, m))
			mvlist.append(m);
		cf.cfile.abortif('!PyTuple_Check(%s) || !PyTuple_Size(%s) == %d' % (inm.ptr(), inm.ptr(), len(self.members)))
		i = 0
		for m, r in self.members:
			cf.cfile.iput('PyObject *p%s = PyTuple_GetItem(%s, %d);\n' % (m, inm.ptr(), i))
			i = i + 1
			pv = NVar('p' + m)
			mv = NVar(m)
			r.p2c(pv, mv)
		#  XXX more fixes needed in generator to avoid extra copies.
		#  memcpy() hack turned out to be unhealthful, as auto vbls
		#  destructors released storage they didn't allocate --
		#  entry_ref.name for example.
		cf.cfile.iput('%s psud(%s);\n' % (self.vtype, string.join(mvlist, ', ')))
		cf.cfile.iput('%s = psud;\n' % onm.val());
		# cf.cfile.indent(-1)

class noderefRules(TupleBase):
	target = ('node_ref',)
	name = 'tpnode_ref'
	vtype = 'node_ref'
	members = (('device', Int32Rules()), ('node', Int64Rules()))

class attrinfoRules(TupleBase):
	target = ('struct attr_info',)
	name = 'tpattr_info'
	vtype = 'struct attr_info'
	members = (('type', UInt32Rules()), ('size', Int64Rules()))

class BPointRules(TupleBase):
	target = ('BPoint',)
	name = 'tpBPoint'
	vtype = 'BPoint'
	members = (('x', IFloatRules()), ('y', IFloatRules()))

class entryrefRules(CTorTuple):
	target = ('entry_ref',)
	name = 'tpentry_ref'
	vtype = 'entry_ref'
	bldval = None
	members = (('device', Int32Rules()), ('directory', Int64Rules()), ('name', CharPtrRules()))

class appinfoRules(CTorTuple):
	target = ('app_info',)
	name = 'tpapp_info'
	vtype = 'app_info'
	members = (('thread', Int32Rules()), ('team', Int32Rules()), ('port', Int32Rules()), ('flags', UInt32Rules()), ('ref', entryrefRules()), ('signature', CharPtrRules()))

class BRectRules(TupleBase):
	target = ('BRect',)
	name = 'tpBRect'
	vtype = 'BRect'
	f = IFloatRules()
	members = (('left', f), ('top', f), ('right', f), ('bottom', f))

class statRules(TupleBase):
	target = ('struct stat',)
	name = 'tpstat'
	vtype = 'struct stat'
	l = Int32Rules()
	L = Int64Rules()
	#  Add crtime to end of posix.stat order;  omit blksize.
	#  crtime sounds interesting and likely to be recognized in this
	#  position;  blksize may be useful, but not obvious where.
	members = (('st_mode', l), ('st_ino', L), ('st_dev', l),
		('st_nlink', l), ('st_uid', l), ('st_gid', l), ('st_size', L),
		('st_atime', l), ('st_mtime', l), ('st_ctime', l),
		('st_crtime', l))

class rgbcolorRules(TupleBase):
	target = ('rgb_color',)
	name = 'tprgb_color'
	vtype = 'rgb_color'
	u = UInt8Rules()
	members = (('red', u), ('green', u), ('blue', u), ('alpha', u))

class scrollbarinfoRules(TupleBase):
	target = ('scroll_bar_info',)
	name = 'tpscroll_bar_info'
	vtype = 'scroll_bar_info'
	b = Int8Rules()
	l = Int32Rules()
	members = (('proportional', b), ('double_arrows', b), ('knob', l), ('min_knob_size', l))

class fontheightRules(TupleBase):
	target = ('font_height',)
	name = 'tpfont_height'
	vtype = 'font_height'
	f = FloatRules()
	members = (('ascent', f), ('descent', f), ('leading', f))

class escapementdeltaRules(TupleBase):
	target = ('escapement_delta',)
	name = 'tpescapement_delta'
	vtype = 'escapement_delta'
	f = FloatRules()
	members = (('nonspace', f), ('space', f))

class fontcacheinfoRules(TupleBase):
	target = ('font_cache_info',)
	name = 'tpfont_cache_info'
	vtype = 'font_cache_info'
	f = FloatRules()
	i = Int32Rules()
	members = (('sheared_font_penalty', i), ('rotated_font_penalty', i), ('oversize_threshold', f), ('oversize_penalty', i), ('cache_size', i), ('spacing_size_threshold', f))

class tunedfontinfoRules(TupleBase):
	target = ('tuned_font_info',)
	name = 'tptuned_font_info'
	vtype = 'tuned_font_info'
	f = FloatRules()
	i = UInt32Rules()
	members = (('size', f), ('shear', f), ('rotation', f), ('flags', i), ('face', i))

# class keyinfoRules(TupleBase):
# 	target = ('key_info',)
# 	name = 'tpkey_info'
# 	vtype = 'key_info'
# 	members = (('modifiers', UInt32Rules()), ('key_states', fixed16Rules()))

class screenidRules(TupleBase):
	target = ('screen_id',)
	name = 'tpscreen_id'
	vtype = 'screen_id'
	members = (('id', UInt32Rules()),)

class versioninfoRules(TupleBase):
	target = ('version_info',)
	name = 'tpversion_info'
	vtype = 'version_info'
	i = UInt32Rules()
	members = (('major', i), ('middle', i), ('minor', i), ('variety', i), ('internal', i), ('short_info', char64Rules()), ('long_info', char256Rules()))

class textrunRules(TupleBase):
	target = ('text_run',)
	name = 'tptext_run'
	vtype = 'text_run'
	fr = CImporter()
	fr.target = ('vBFont',)
	fr.name = 'tpvBFont'
	fr.vtype = 'BFont'
	fr.ptype = 'BFont'
	fr.bldval = None
	members = (('offset', Int32Rules()), ('font', fr), ('color', rgbcolorRules()))

class textrunarrayRules(RuleBase):
	target = ('text_run_array',)
	name = 'tptext_run_array'
	vtype = 'text_run_array*'
	ptype = 'list'
	storage = Variable.HEAP
	def p2c(self, inm, onm):
		cf.cfile.abortif('!PyList_Check(%s)' % inm.ptr())
		cf.cfile.iput('else {\n')
		cf.cfile.indent(1)
		cf.cfile.iput('int n = PyList_Size(%s);\n' % inm.ptr())
		#  OK if n == 0, right?
		cf.cfile.iput('%s = (text_run_array *) malloc(sizeof(text_run) * n + 4);\n' % (onm.ptr(),))
		cf.cfile.abortif('!%s' % onm.ptr())
		cf.cfile.iput('(%s)->count = n;\n' % onm.ptr())
		cf.cfile.iput('int i;\n')
		cf.cfile.iput('for (i = 0; i < n; ++i) {\n')
		cf.cfile.indent(1)
		saveabort = cf.cfile.abortexpr
		cf.cfile.abortexpr = 'goto fail;\n'
		cf.cfile.iput('PyObject *ptextrun = PyList_GetItem(%s, i);\n' % inm.ptr())
		# pt = NVar('ptextrun')
		pt = Variable('PyObject*', 'ptextrun')
		cf.cfile.iput('text_run *textrun = &(%s)->runs[i];\n' % onm.ptr())
		ct = Variable('text_run*', 'textrun')
		ct.classify(textrunRules(), 1)
		ct.p2c(pt)
		cf.cfile.abortexpr = saveabort
		cf.cfile.indent(-1)
		cf.cfile.iput('}\n')
		cf.cfile.indent(-1)
		cf.cfile.iput('}\n')
		cf.cfile.iput('goto nofail;\n')
		cf.cfile.put('fail:\n')
		cf.cfile.iput('free(%s);\n' % inm.ptr())
		cf.cfile.iput(cf.cfile.abortexpr)
		cf.cfile.put('nofail:\n')
	def c2p(self, inm, onm, dim):
		# "dim" is actually the size in bytes!
		cf.cfile.iput('int i;\n')
		cf.cfile.iput('%s = PyTuple_New(%s->count);\n' % (onm.ptr(), inm.ptr()))
		cf.cfile.iput('for (i = 0; i < %s->count; ++i) {\n' % inm.ptr())
		cf.cfile.indent(1)
		cf.cfile.iput('text_run *textrun = &%s->runs[i];\n' % inm.ptr())
		ct = Variable('text_run*', 'textrun')
		ct.classify(textrunRules, 1)
		cf.cfile.iput('PyObject *ptextrun;\n')
		pt = Variable('PyObject*', 'ptextrun')
		ct.c2p(pt)
		cf.cfile.iput('PyTuple_SetItem(%s, i, %s);\n' % (onm.ptr(), pt.ptr()))
		cf.cfile.indent(-1)
		cf.cfile.iput('}\n')
		cf.cfile.iput('free(%s);\n' % inm.ptr())

# To do:
#
# typedef struct color_map {
#                 int32           id;
#                 rgb_color       color_list[256];
#                 uint8           inversion_map[256];
#                 uint8           index_map[32768];
# } color_map;
#
# (why?)
# struct key_info {
#         uint32  modifiers;
#         uint8   key_states[16];
# }
#
# struct menu_info {
#         float           font_size;
#         font_family     f_family;
#         font_style      f_style;
#         rgb_color       background_color;
#         int32           separator;
#         bool            click_to_open;
#         bool            triggers_always_shown;
# };


class ListBase(RuleBase):
	# List base expects:
	# target: blist_team_id, for example.
	# itemtype: team_id
	vtype = 'BList'
	def declare(self, inm):
		# cf.cfile.iput('BList *%s = new BList();\n' % inm.name)
		return ['BList *%s = new BList()' % inm.name]
	def p2c(self, inm, onm):
		cf.cfile.iput('yikes, don\'t know how to make C BList.\n')
	def c2p(self, inm, onm, dim):
		import sggen
		bldval = ''
		mv = []
		pmx = 1
		cf.cfile.iput('int count = %s->CountItems();\n' % inm.ptr())
		cf.cfile.iput('%s = PyList_New(count);\n' % onm.ptr())
		cf.cfile.abortif('!%s' % onm.ptr())
		cf.cfile.iput('int i;\n')
		cf.cfile.iput('for (i = 0; i < count; ++i) {\n')
		cf.cfile.indent(1)
		cm = Variable(self.itemtype, 'item')
		cm.classify()
		cf.cfile.iput('%s item;\n' % self.itemtype)
		pm = Variable('PyObject *', 'pytem')
		cf.cfile.iput('PyObject *pytem;\n')
		cf.cfile.iput('item = (%s)%s->ItemAt(i);\n' % (self.itemtype, inm.ptr()))
		cm.c2p(pm)
		cf.cfile.iput('PyList_SetItem(%s, i, pytem);\n' % onm.ptr())
		cf.cfile.indent(-1)
		cf.cfile.iput('}\n')

class TeamIDListRules(ListBase):
	target = ('blist_team_id',)
	itemtype = 'team_id'
	ptype = 'list'
	name = 'tpteamidlist'

class BMessageListRules(ListBase):
	target = ('blist_BMessage',)
	itemtype = 'BMessage*'
	ptype = 'list'
	name = 'tpbmessagelist'

class RuleSet:
	def __init__(self):
		self.dict = {}
	def add(self, rule, name):
		self.dict[name] = rule
	def query(self, name):
		t = self.dict.get(name)
		if t:
			return t
		if name[:1] == 'B':
			c = CImporter()
			c.target = name
			c.name = 'tp' + name
			c.vtype = name + '*'
			c.ptype = name
			self.dict[name] = c
			return c
		raise KeyError, name

def Ruleset():
	cf.rules = RuleSet()
	for ck, cv in globals().items():
		if ck[-5:] == 'Rules':
			ob = cv()
			for t in cv.target:
				cf.rules.add(ob, t)
if __name__ == '__main__':
	fp = sys.stdout
	fp.write('# automatically generated by sgrules.py\n\n')
	fp.write('from structuple import Structuple\n\n')
	for ck, cv in globals().items():
		if ck[-5:] == 'Rules' and hasattr(cv, 'classgen'):
			ob = cv()
			ob.classgen(fp)
else:
	Ruleset()
