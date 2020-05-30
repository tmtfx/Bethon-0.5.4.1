#  Default target makes another Makefile, with rules for each and every
#  .dx file in src.
#
#  The "bld" script is equivalent to "alias bld='make -f xmakefile'".
#  It's a short route to the generated makefile when you need to build
#  just one specific piece.
#

all: xmakefile
	make -f xmakefile

install: xmakefile
	make -f xmakefile install

FORCE:

xmakefile: FORCE
	python mkmake

clean:
	rm -f *.cpp *.o *.so *.m4 xmakefile
