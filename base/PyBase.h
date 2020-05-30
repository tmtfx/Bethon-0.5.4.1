#ifndef _PYBASE_H_
#define _PYBASE_H_

//
//  Copyright 1998 by Donn Cave, Seattle, Washington, USA.
//  All Rights Reserved.  Permission to use, copy, modify and distribute
//  is hereby granted, provided that above copyright appear in all copies.
//

#include <support/Archivable.h>
#include "Python.h"

struct BaseObject;

#define MAXBASETYPES 11
struct baseItem {
    char name[32];
    int offset;
    PyTypeObject *type;
};

#include "BpyBase.h"
#define MOTHERBASE void
#define BEBOSTAMP "like me?"

#define BEVOIDINT 0xc2c5d6cf
#define BEVOIDEXT 0xc2c5d6ce
//  Object header with a C linkage and pseudo-base class references.
//  This has to be consistent in order to refer this object
//  back to C-Python pseudo-base classes.
//
#define BaseObject_HEAD PyObject_HEAD \
  MOTHERBASE *bevoid; \
  uint32 bevoidness;  \
  struct baseItem *base;

struct BaseObject {
    BaseObject_HEAD
};

#define INTERNAL_BEPTR(o) ((o)->bevoidness == BEVOIDINT)
#define EXTERNAL_BEPTR(o) ((o)->bevoidness == BEVOIDEXT)
#define SETEXT_BEPTR(o,c)   ( (o)->bevoid = c, (o)->bevoidness = BEVOIDEXT )
#define SETINT_BEPTR(o,c)   ( (o)->bevoid = c, (o)->bevoidness = BEVOIDINT )
#define BINDINT_BEPTR(o,c)  (c)->bindSelf((PyObject *) o);

//  Base for exported C function table;  when looking up the base classes
//  for a derived pseudo class, their simpleattr functions are found through
//  this table exported as a CObject during module initialization.
//
struct BaseFunctions {
    PyObject *(*FromIt)(const void *, int);
    void *(*AsIt)(PyObject *);
    PyTypeObject *type;
};

#define SysBaseObject_HEAD BaseObject_HEAD \
    int sysref;

//  Objects held by system; particularly, subject to deletion by system.
//  See BpySRVBase
//
struct SysBaseObject {
    SysBaseObject_HEAD
};

//  Objects for system dispatching threads.  See BpyLSRVBase.
//
struct LooperBaseObject {
    SysBaseObject_HEAD
    PyThreadState *tstate;
};

void Base_init(baseItem *, const char *, int, PyTypeObject *);
PyTypeObject *Base_initFromName(baseItem *, const char *, int);

#endif
