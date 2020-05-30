#
#  Make dictionary from BMessage attributes.
#
import BMessage

import hollerith

B_ANY_TYPE = hollerith.str2int('ANYT')
B_ASCII_TYPE = hollerith.str2int('TEXT')
B_BOOL_TYPE = hollerith.str2int('BOOL')
B_CHAR_TYPE = hollerith.str2int('CHAR')
B_COLOR_8_BIT_TYPE = hollerith.str2int('CLRB')
B_DOUBLE_TYPE = hollerith.str2int('DBLE')
B_FLOAT_TYPE = hollerith.str2int('FLOT')
B_GRAYSCALE_8_BIT_TYPE = hollerith.str2int('GRYB')
B_INT64_TYPE = hollerith.str2int('LLNG')
B_INT32_TYPE = hollerith.str2int('LONG')
B_INT16_TYPE = hollerith.str2int('SHRT')
B_INT8_TYPE = hollerith.str2int('BYTE')
B_MESSAGE_TYPE = hollerith.str2int('MSGG')
B_MESSENGER_TYPE = hollerith.str2int('MSNG')
B_MIME_TYPE = hollerith.str2int('MIME')
B_MONOCHROME_1_BIT_TYPE = hollerith.str2int('MNOB')
B_OBJECT_TYPE = hollerith.str2int('OPTR')
B_OFF_T_TYPE = hollerith.str2int('OFFT')
B_PATTERN_TYPE = hollerith.str2int('PATN')
B_POINTER_TYPE = hollerith.str2int('PNTR')
B_POINT_TYPE = hollerith.str2int('BPNT')
B_RAW_TYPE = hollerith.str2int('RAWT')
B_RECT_TYPE = hollerith.str2int('RECT')
B_REF_TYPE = hollerith.str2int('RREF')
B_32_BIT_TYPE = hollerith.str2int('RGBB')
B_COLOR_TYPE = hollerith.str2int('RGBC')
B_SIZE_T_TYPE = hollerith.str2int('SIZT')
B_SSIZE_T_TYPE = hollerith.str2int('SSZT')
B_STRING_TYPE = hollerith.str2int('CSTR')
B_TIME_TYPE = hollerith.str2int('TIME')
B_UINT64_TYPE = hollerith.str2int('ULLG')
B_UINT32_TYPE = hollerith.str2int('ULNG')
B_UINT16_TYPE = hollerith.str2int('USHT')
B_UINT8_TYPE = hollerith.str2int('UBYT')
B_MEDIA_PARAMETER_TYPE = hollerith.str2int('BMCT')
B_MEDIA_PARAMETER_WEB_TYPE = hollerith.str2int('BMCW')
B_MEDIA_PARAMETER_GROUP_TYPE = hollerith.str2int('BMCG')

table = {
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

def contents(msg):
	c = {}
	i = 0
	while 1:
		try:
			name, type, count = msg.GetInfo(B_ANY_TYPE, i)
		except BMessage.error:
			name = None
		if name is None:
			break
		i = i + 1
		try:
			fun = getattr(msg, 'Find' + table[type])
		except:
			fun = None
		if fun is None:
			cl = [None]*count
		else:
			cl = []
			for j in range(count):
				cl.append(fun(name, j))
		c[name] = (type, tuple(cl))
	return c
