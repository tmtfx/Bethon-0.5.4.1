//
//  Utility to set BEOS:PPATH to /boot/home/config/bin/python
//  That's used by Tracker to find the interpreter.
//

#include <stdio.h>

#include <storage/File.h>
#include <storage/AppFileInfo.h>

int
main(int argc, char **argv)
{
	BFile app(argv[1], B_WRITE_ONLY);
	BAppFileInfo info(&app);
	BEntry Python("/boot/home/config/bin/python", 0);
	entry_ref python;
	Python.GetRef(&python);
	if (info.SetAppHint(&python) < B_OK)
		perror("python");
	return 0;
}
