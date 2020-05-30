all: pythonversion
	cd base; make
	cd build; make
	cd symbols; make

install: all
	cd build; make install
	cd symbols; make install

pythonversion:
	python -c 'import sys; open("pythonversion", "w").write("PYTHONVERSION=%s.%s\n" % sys.version_info[:2])'

clean:
	cd base; make clean
	cd build; make clean
	cd gen; make clean
	cd symbols; make clean
