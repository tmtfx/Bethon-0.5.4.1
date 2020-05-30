#  Copyright 1999 by Donn Cave, Seattle, Washington, USA.
#  All rights reserved.  Permission to copy, modify and distribute this
#  material is hereby granted, without fee, provided that the above
#  copyright notice appear in all copies.

import string
import sys

from BMessenger import BMessenger
from BMessage import BMessage
from BPropertyInfo import BPropertyInfo

from AppKit import B_NO_SPECIFIER,B_DIRECT_SPECIFIER,B_INDEX_SPECIFIER,B_REVERSE_INDEX_SPECIFIER,B_RANGE_SPECIFIER,B_REVERSE_RANGE_SPECIFIER,B_NAME_SPECIFIER,B_ID_SPECIFIER,B_GET_SUPPORTED_SUITES,B_CREATE_PROPERTY,B_DELETE_PROPERTY,B_GET_PROPERTY,B_SET_PROPERTY,B_EXECUTE_PROPERTY,B_COUNT_PROPERTIES,B_REPLY,B_NO_REPLY,B_MESSAGE_NOT_UNDERSTOOD

from message import Message

class Scriptable:
	scr_lookup = { B_NO_SPECIFIER: 'B_NO_SPECIFIER',
	B_DIRECT_SPECIFIER: 'B_DIRECT_SPECIFIER',
	B_INDEX_SPECIFIER: 'B_INDEX_SPECIFIER',
	B_REVERSE_INDEX_SPECIFIER: 'B_REVERSE_INDEX_SPECIFIER',
	B_RANGE_SPECIFIER: 'B_RANGE_SPECIFIER',
	B_REVERSE_RANGE_SPECIFIER: 'B_REVERSE_RANGE_SPECIFIER',
	B_NAME_SPECIFIER: 'B_NAME_SPECIFIER',
	B_ID_SPECIFIER: 'B_ID_SPECIFIER',
	B_GET_SUPPORTED_SUITES: 'B_GET_SUPPORTED_SUITES',
	B_CREATE_PROPERTY: 'B_CREATE_PROPERTY',
	B_GET_PROPERTY: 'B_GET_PROPERTY',
	B_DELETE_PROPERTY: 'B_DELETE_PROPERTY',
	B_SET_PROPERTY: 'B_SET_PROPERTY',
	B_EXECUTE_PROPERTY: 'B_EXECUTE_PROPERTY',
	B_COUNT_PROPERTIES: 'B_COUNT_PROPERTIES'}
	def __init__(self, mr, specstack, name = None):
		self.__dict__['scr_properties'] = ()
		self.__dict__['scr_mr'] = mr
		self.__dict__['scr_specstack'] = specstack
		if name is None:
			name = self.__class__.__name__
		self.__dict__['scr_name'] = name
		if specstack:
			msg = self.scr_get(('Suites',))
		else:
			msg = BMessage(B_GET_SUPPORTED_SUITES)
			msg = self.scr_msa(msg, None)
		self.__dict__['scr_properties'] = self.scr_suites(msg)
	def scr_suites(self, msg):
		error = msg.FindInt32('error')
		if error:
			raise SystemError, 'Scripting error 0x%08x' % error
		p = BPropertyInfo()
		t, n = msg.GetInfo('messages')
		pl = ()
		for i in range(n):
			p = BPropertyInfo()
			msg.FindFlat('messages', i, p)
			pl = pl + p.Properties()
		return pl
	def __repr__(self):
		pl = []
		for name, commands, specifiers, usage, extra in self.scr_properties:
			cl = []
			for c in commands:
				cl.append(self.scr_lookup[c])
			commands = string.join(cl, ', ')
			cl = []
			for c in specifiers:
				cl.append(self.scr_lookup[c])
			specifiers = string.join(cl, ', ')
			pl.append('%s: (%s) (%s) %s %s' % (name, commands, specifiers, usage, extra))
		return '<%s: (%s)>' % (self.scr_name, string.join(pl, ', '))
	def scr_msa(self, what, spec):
		smsg = BMessage(what)
		# print '+->', self.scr_mr
		if spec:
			# print '+', spec
			apply(smsg.AddSpecifier, spec)
		for spec in self.scr_specstack:
			# print '+ ...', spec
			apply(smsg.AddSpecifier, spec)
		msg = self.scr_mr.SendMessageReply(smsg)
		# msg.PrintToStream()
		if msg.what == B_REPLY or msg.what == B_NO_REPLY:
			return msg
		elif msg.what == B_MESSAGE_NOT_UNDERSTOOD:
			raise ValueError, msg.FindString('message') + ': ' + repr(spec)
		else:
			# msg.PrintToStream()
			raise ValueError, msg.what
	def scr_get(self, spec):
		msg = BMessage(B_GET_PROPERTY)
		return self.scr_msa(msg, spec)
	def scr_getvalue(self, spec):
		msg = self.scr_get(spec)
		if msg.what == B_REPLY:
			# XXX 'result' is always exactly 1 value?
			return Message(msg).get('result')[0]
		else:
			return None
	def scr_set(self, data, spec):
		msg = BMessage(B_SET_PROPERTY)
		m = Message(msg)
		m.add('data', data)
		return self.scr_msa(msg, spec)
	def scr_count(self, spec):
		msg = BMessage(B_COUNT_PROPERTIES)
		return self.scr_msa(msg, spec).FindInt32('result')
	def __getattr__(self, attr):
		for name, cmd, spec, usage, extra in self.scr_properties:
			if name == attr and B_GET_PROPERTY in cmd:
				return self.scr_getvalue((attr,))
		for name, cmd, spec, usage, extra in self.scr_properties:
			if name == attr and B_COUNT_PROPERTIES in cmd:
				return ScriptableSequence(self, attr)
		raise AttributeError, attr
	def __setattr__(self, attr, value):
		for name, cmd, spec, usage, extra in self.scr_properties:
			if name == attr and B_SET_PROPERTY in cmd:
				msg = self.scr_set(value, (attr,))
				# msg.PrintToStream()

class ScriptableSequence:
	def __init__(self, scriptable, attr):
		self.scriptable = scriptable
		self.attribute = attr
	def __getitem__(self, i):
		return self.scriptable.scr_getvalue((self.attribute, i))
	def __setitem__(self, i, val):
		msg = self.scriptable.scr_set(val, (self.attribute, i))
		# msg.PrintToStream()
