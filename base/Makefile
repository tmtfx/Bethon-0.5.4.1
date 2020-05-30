PYTHONVERSION=2.2
-include ../pythonversion

OPT=		-O
DEFS=		-DHAVE_CONFIG_H
INCLDIR=	/boot/system/develop/headers/python${PYTHONVERSION}
CFLAGS=		$(OPT) -I. -I$(INCLDIR) $(DEFS)

all: PyBase.o PyMisc.o BpyBase.o

PyBase.o: PyBase.cpp PyBase.h BpyBase.h
	$(CC) -c $(CFLAGS) PyBase.cpp
PyMisc.o: PyMisc.cpp PyMisc.h
	$(CC) -c $(CFLAGS) PyMisc.cpp
BpyBase.o: BpyBase.cpp BpyBase.h
	$(CC) -c $(CFLAGS) BpyBase.cpp

clean:
	rm -f *.o
