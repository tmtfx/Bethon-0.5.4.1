#
#  General definitions.
#
#  Python version:  works with 1.5.2 and 2.0, default is 2.0.
#  If you're using something other than the default, you can put a file
#  in the top directory called "pythonversion", with contents
#  PYTHONVERSION=2.2
#  That will then override the default, via the include statement below.
#  I use "-include" (instead of "include") so it's OK if the file isn't
#  there.
#
PYTHONVERSION=2.2
-include ../pythonversion

GENDEPS = ../gen/sggen.py ../gen/sgrules.py ../gen/sgparse.py ../gen/sgvar.py ../gen/module.m4 ../gen/defs.m4
BASEOBJS = ../base/PyBase.o ../base/PyMisc.o ../base/BpyBase.o
BASEINCL = ../base/BpyBase.h ../base/PyBase.h

# -ltracker for FilePanel, -ldevice for SerialPort
LIBS = -L/system/lib -nodefaultlibs -lbe -ltracker -ldevice -ltranslation -lroot

OPT = -O
PYTHONCFLAGS = -DHAVE_CONFIG -I/boot/system/develop/headers/python$(PYTHONVERSION)
CFLAGS = $(OPT) -I../base $(PYTHONCFLAGS)

VPATH=../source

.SUFFIXES: .dx module.so

.dx.cpp:
	PYTHONPATH=../gen python ../gen/sg $<
	m4 -I../gen -Dtemplate=module.m4 xxdefs.m4 > $@
.cpp.o:
	$(CC) -c $(CFLAGS) $< -o $@
