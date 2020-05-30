//  This simple program is compile-linked to the Python interpreter,
//  so it can provide a "binary" image for the Python program it really
//  runs, and all kinds of BeOS loading semantics can be attached here -
//  mime types, icons, single-launch, bla bla.  This example is the most
//  minimal, crude but reasonably effective.
//
//  It's also possible to implement BApplication in C++ here, then import
//  the main Python module (now rewritten of course to omit its BApplication
//  class wrapper) and call its exported  methods.  I don't see anything
//  to be gained from this, but there's a lot I don't know.  Anyway, to do
//  it you need to add a tweak to BApplication.cpp, to set "be_app" from
//  the FromBApplication() function.

#include <sys/file.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h> /* creat */

#ifndef PYTHON_INSTALL_PREFIX
#define PYTHON_INSTALL_PREFIX "/boot/home/config"
#endif

#include <Python.h>

static void
setup_log()
{
	static const char logfile[] = APPLICATION_LOG;

	int efd;
	efd = creat(logfile, 0000);
	if (efd >= 0) {
		dup2(efd, 1);
		dup2(efd, 2);
	} else
		perror(logfile);
}

static void
setup_interpreter(int argc, char **argv, char *appdir)
{
	char path[256];
	static const char prefix[] = PYTHON_INSTALL_PREFIX;
	char python[12];

	Py_SetProgramName(argv[0]);
	Py_Initialize();
	PySys_SetArgv(argc, argv);

	sprintf(python, "python%d.%d", PY_MAJOR_VERSION, PY_MINOR_VERSION);
#if PY_MAJOR_VERSION == 1
	sprintf(path, "%s:%s/lib/%s:%s/lib/%s/plat-beos:%s/lib/%s/lib-dynload",
#else
# ifdef __HAIKU__
	sprintf(path, "%s:%s/lib/%s:%s/lib/%s/plat-haiku1:%s/lib/%s/lib-dynload",
# else
#  ifndef B_BEOS_VERSION_5
#    define B_BEOS_VERSION_5 0x0500
#  endif
#  ifndef B_BEOS_VERSION_6
#    define B_BEOS_VERSION_6 0x0600
#  endif
#  if B_BEOS_VERSION >= B_BEOS_VERSION_4 && B_BEOS_VERSION < B_BEOS_VERSION_5
	sprintf(path, "%s:%s/lib/%s:%s/lib/%s/plat-beos4:%s/lib/%s/lib-dynload",
#  elif B_BEOS_VERSION >= B_BEOS_VERSION_5 && B_BEOS_VERSION < B_BEOS_VERSION_6
	sprintf(path, "%s:%s/lib/%s:%s/lib/%s/plat-beos5:%s/lib/%s/lib-dynload",
#  elif B_BEOS_VERSION >= B_BEOS_VERSION_6
	sprintf(path, "%s:%s/lib/%s:%s/lib/%s/plat-beos6:%s/lib/%s/lib-dynload",
#  endif
# endif
#endif
		appdir,
		prefix, python,
		prefix, python,
		prefix, python);
	PySys_SetPath(path);
}

int
main(int argc, char **argv)
{
	FILE *py;
	char *nm;
	static char progfile[] = APPLICATION;
	static char defdir[] = ".";
	char *progbase, *progdir;

	py = fopen(progfile, "r");
	if (!py) {
		perror(progfile);
		exit(1);
	}

	progbase = strrchr(progfile, '/');
	if (progbase) {
		*progbase++ = 0;
		progdir = progfile;
	} else {
		progbase = progfile;
		progdir = defdir;
	}

	setup_log();
	setup_interpreter(argc, argv, progfile);

	PyRun_AnyFile(py, progbase);
	if (PyErr_Occurred()) {
		PyErr_Print();
		exit(1);
	} else
		exit(0);
}
