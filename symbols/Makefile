#
#  Make Python modules that define various B_symbols.
#  Each corresponds to a "kit" and defines the symbols
#  in all the include files in the kit's directory,
#  but that's only a convention.
#
#  See mkdef for a vague description of the process.
#

HDR = /boot/system/develop/headers/os

all: AppKit.py InterfaceKit.py StorageKit.py SupportKit.py

AppKit.py:
	./mkdef $@ $(HDR)/app/*.h

InterfaceKit.py:
	./mkdef $@ $(HDR)/interface/*.h

StorageKit.py:
	./mkdef $@ $(HDR)/storage/*.h

SupportKit.py:
	./mkdef $@ $(HDR)/support/*.h
	./tempfix

MailKit.py:
	./mkdef $@ $(HDR)/mail/*.h

install: all
	./install *.py

clean:
	rm -f *.py* xx*
