#  Copyright 1999 by Donn Cave, Seattle, Washington, USA.
#  All rights reserved.  Permission to copy, modify and distribute this
#  material is hereby granted, without fee, provided that the above
#  copyright notice appear in all copies.

from types import *

import BMessage


from SupportKit import B_ANY_TYPE,B_ASCII_TYPE,B_BOOL_TYPE,B_CHAR_TYPE,B_DOUBLE_TYPE,B_FLOAT_TYPE,B_INT64_TYPE,B_INT32_TYPE,B_INT16_TYPE,B_INT8_TYPE,B_MESSAGE_TYPE,B_MESSENGER_TYPE,B_MIME_TYPE,B_OBJECT_TYPE,B_OFF_T_TYPE,B_PATTERN_TYPE,B_POINTER_TYPE,B_POINT_TYPE,B_RAW_TYPE,B_RECT_TYPE,B_REF_TYPE,B_SIZE_T_TYPE,B_SSIZE_T_TYPE,B_STRING_TYPE,B_TIME_TYPE,B_UINT64_TYPE,B_UINT32_TYPE,B_UINT16_TYPE,B_UINT8_TYPE

actors = {
	B_STRING_TYPE: 'String',
	B_INT64_TYPE: 'Int64',
	B_TIME_TYPE: 'Time',
	B_UINT64_TYPE: 'Uint64',
	B_INT32_TYPE: 'Int32',
	B_INT16_TYPE: 'Int16',
	B_INT8_TYPE: 'Int8',
	B_UINT32_TYPE: 'Uint32',
	B_UINT16_TYPE: 'Uint16',
	B_UINT8_TYPE: 'Uint8',
	B_BOOL_TYPE: 'Bool',
	B_DOUBLE_TYPE: 'Double',
	B_FLOAT_TYPE: 'Float',
	B_POINT_TYPE: 'Point',
	B_RECT_TYPE: 'Rect',
	B_REF_TYPE: 'Ref',
	B_MESSAGE_TYPE: 'Message',
	B_MESSENGER_TYPE: 'Messenger',
	B_MIME_TYPE: 'String'
}

stdtypes = {
	StringType : B_STRING_TYPE,
	IntType : B_INT32_TYPE,
	FloatType: B_DOUBLE_TYPE,
	TupleType: ((4, B_RECT_TYPE), (2, B_REF_TYPE))
}

class Message:
	def __init__(self, msg):
		self.msg = msg
		self.xdict = {}
	def dict(self):
		if not self.xdict:
			i = 0
			while 1:
				try:
					name, type, count = self.msg.GetInfo(B_ANY_TYPE, i)
				except BMessage.error:
					name = None
				if name is None:
					break
				i = i + 1
				self.xdict[name] = (type, tuple(self.value(name, type, count)))
		return self.xdict
	def get(self, name):
		type, count = self.msg.GetInfo(name)
		return self.value(name, type, count)
	def add(self, name, value):
		betype = stdtypes.get(type(value))
		if betype is None:
			if type(value) == type(self.msg):
				betype = B_MESSAGE_TYPE
			else:
				raise TypeError, 'No conversion for type of %s' % value
		fun = getattr(self.msg, 'Add' + actors[betype])
		fun(name, value)
	def value(self, name, type, count):
		try:
			fun = getattr(self.msg, 'Find' + actors[type])
		except:
			fun = None
		if fun is None:
			cl = [None]*count
		else:
			cl = []
			for j in range(count):
				cl.append(fun(name, j))
		return cl
