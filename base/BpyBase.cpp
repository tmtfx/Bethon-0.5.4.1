//  Copyright 1998-1999 by Donn Cave, Seattle, Washington, USA.
//  All rights reserved.  Permission to copy, modify and distribute this
//  material is hereby granted, without fee, provided that the above
//  copyright notice appear in all copies.

//  Base class to subclass along with Be API class that defines virtual
//  functions.  Its purpose is to allow a Python class to implement these
//  virtual functions.
//
#include "Python.h"
#include <stdio.h>
#include <string.h>

#include "BpyBase.h"

//  Look for virtual functions that may have been defined in the
//  Python class that this thing is attached to.
//
//  I check the class first, on the assumption that such functions
//  will be defined there as well.  This avoids the wrapper lookup
//  back into the C object when the attribute isn't in the wrapper.
//  There must be a better way to get class than looking up "__class__".
//
int
BpyVBase::VFNInventory(PyInstanceObject *inst, PyObject **vfn,
	struct vfnLookupTbl *tbl, int nlup)
{
    instance = inst;
    // Py_INCREF((PyObject *) inst);
    PyObject *classe = (PyObject *) instance->in_class;
    if (!classe)
	return -1;
    int i, count;
    for (i = 0, count = 0; i < nlup; ++i) {
	PyObject *fun = PyObject_GetAttrString(classe, tbl[i].name);
	PyObject *meth;
	if (fun) {
	    meth = PyObject_GetAttrString((PyObject *) instance, tbl[i].name);
	    if (!PyMethod_Check(meth)) {
		PyErr_SetString(PyExc_TypeError, tbl[i].name);
		return -1;
	    }
	} else {
	    meth = 0;
	    PyErr_Clear();
	}
	vfn[tbl[i].index] = meth;
	if (meth) {
	    // slprintf(" Python virtual function: %s\n", tbl[i].name);
	    // Py_INCREF(meth);
	    // Refs here can be circular and don't help.
	    // Pretty sure getattr() above already made one anyway,
	    // so the question really is whether a DECREF() would
	    // work here.
	    ++count;
	}
    }
    return count;
}
