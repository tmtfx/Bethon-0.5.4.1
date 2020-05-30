//  Copyright 1999 by Donn Cave, Seattle, Washington, USA.
//  All rights reserved.  Permission to copy, modify and distribute this
//  material is hereby granted, without fee, provided that the above
//  copyright notice appear in all copies.

#include <string.h>

#include "Python.h"
#include "PyMisc.h"

//  Check actual against formal parameters.
int
ParseTuple(PyObject *argv, struct InputParam *par, int np)
{
	int i;
	int n = PyTuple_Size(argv);
	for (i = 0; i < np && par[i].fun; ++i) {
		struct InputParam *p = &par[i];
	//  Possible optimization - previous call already validated this
	//  same object, from reference in another parameter.
	//  It could be a good idea anyway.  Caller would need to provide
	//  full overload table.
	//  Cheap trick alternative - caller initializes to 0,
	//  so non-0 values are successful conversions.  The
	//  case of int 0 is obviously not accounted for, but
	//  that's possibly not as expensive as others.

		//  Call specified converter, put result in "res"
		if (i < n) {
			PyObject *arg = PyTuple_GetItem(argv, i);
			if (arg == Py_None) {
				if (p->res)
					memcpy(p->var, p->res, p->size);
				else
					memset(p->var, 0, p->size);
			} else {
				if (p->fun(p, PyTuple_GetItem(argv, i)))	
					p->res = p->var;
				else {
					//  Forget any error here, since
					//  this is not going to be raised.
					//  (If this is not as good of an
					//  idea as I think, then turn off
					//  the unraised exception complaint
					//  in Base_initFromName.)

					PyErr_Clear();
					return 0;
				}
			}
		} else if (p->res)
	//  memcpy() will lose with entry_ref et al., thanks to destructors.
	//  Maybe solve with 3rd param to "fun", which can cast and assign -
	//  assignment operators presumably account for storage issues.
			memcpy(p->var, p->res, p->size);
		else
			return 0;
	}
	return i >= n;
}
