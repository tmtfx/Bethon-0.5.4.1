//  Copyright 1998-1999 by Donn Cave, Seattle, Washington, USA.
//  All rights reserved.  Permission to copy, modify and distribute this
//  material is hereby granted, without fee, provided that the above
//  copyright notice appear in all copies.

//  Support functions for cross-module inheritance of ordinary class
//  methods and attributes.
//

#include <stdio.h>
#include <string.h>

#include "Python.h"

#include "PyBase.h"

void
Base_init(struct baseItem *base, const char *name, int offset, PyTypeObject *type)
{
    int i;

    if (type) {
	//  Find first empty slot.
	//
	for (i = 0; i < MAXBASETYPES && base[i].name[0]; ++i)
	    ;
	if (i < MAXBASETYPES) {
	    int len = strlen(name);
	    struct baseItem *ibase = &(base[i]);
	    if (len >= sizeof(ibase->name))
		len = sizeof(ibase->name) - 1;
	    memcpy(ibase->name, name, len);
	    ibase->name[len] = 0;
	    ibase->offset = offset;
	    ibase->type = type;
	} else
	    fprintf(stderr, "\"%s\": Base limit exceeded.\n", name);
    } else {
	for (i = 0; i < MAXBASETYPES && base[i].name[0]; ++i) {
	    if (strcmp(base[i].name, name) == 0) {
		base[i].offset = offset;
		return;
	    }
	}
	fprintf(stderr, "\"%s\": Base not found in 2nd pass!\n", name);
    }
}

PyTypeObject *
Base_initFromName(struct baseItem *base, const char *name, int offset)
{
    //  Get module and load base support.
    //
    char simple[128], *mod;
    struct BaseFunctions *basefun;
    if (PyErr_Occurred()) {
	// Sloppy bind attribute lookup, etc.
	fprintf(stderr, "-- \"%s\" base init: cleaning up unraised errors.\n", name);
	PyErr_Print();
	PyErr_Clear();
    }
    basefun = (struct BaseFunctions *) PyCObject_Import((char *)name, "functions");
    if (basefun) {
        if (PyErr_Occurred())
	    fprintf(stderr, "Error in \"%s\" import\n", name);
	Base_init(base, name, offset, basefun->type);
	return basefun->type;
    } else {
	PyErr_Clear();
	return 0;
    }
}
