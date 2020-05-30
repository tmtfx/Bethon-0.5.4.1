#ifndef _PYMISC_H_
#define _PYMISC_H_

struct InputParam {
	void *var;			//  Storage.
	void *res;			//  Default if any.
	const char *tname;		//  Name for error report.
	int (*fun)(struct InputParam *, PyObject *); //  P2C converter.
	int size;			//  Size of storage.
};

int ParseTuple(PyObject *, struct InputParam *, int);

#endif
