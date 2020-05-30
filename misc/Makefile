PYTHONVERSION=2.2
-include ../pythonversion

OPT=-O
INCLUDE=-I- -I/boot/common/include/python$(PYTHONVERSION)
DEFS=-DHAVE_CONFIG $(INCLUDE)
CFLAGS=$(OPT) $(DEFS)
LIBS=-L/boot/common/lib -lpython$(PYTHONVERSION) -ltextencoding -lnetwork -lbe -ltracker -lroot

# Like, you can leave this file here if you want.
BPYSRC = ../
APP = $(BPYSRC)/misc/app.cpp

hello_app: hello_app.o hello.pk
	$(CC) -o $@ hello_app.o $(LIBS)
	../test/load_attr hello_app < hello.pk
hello_app.o: $(APP)
	$(CC) -c $(CFLAGS) $(APP) -o $@ -DAPPLICATION='"'$$PWD'/hello"' -DAPPLICATION_LOG='"/var/log/Hello"'

clean:
	rm -f *.o *.pyc hello_app
