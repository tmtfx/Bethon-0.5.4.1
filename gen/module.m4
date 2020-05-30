dnl  Copyright 2002 by Donn Cave, Seattle, Washington, USA.
dnl  All rights reserved.  Permission to copy, modify and distribute this
dnl  material is hereby granted, without fee, provided that the above
dnl  copyright notice appear in all copies.

//
//  C++ code automatically generated.
//
#include <stdio.h>
#include <string.h>

includes(BE_INCLUDES)

dnl  Virtual functions need be_app, to quit if something goes wrong.
dnl
ifdef(`VFUNS',``#'include <app/Application.h>')

`#'include <Python.h>
`#'include "PyBase.h"
`#'include "PyMisc.h"

imports(IMPORTS)

`#'include "BpyBase.h"
ifdef(`VFUNS',
`// Class has virtual methods - e.g., handler.
enum {
   venums(VFUNS)
   NVFN
};
//
')

define(`MODULENAME', `B'CLASS)
define(`APINAME', `B'CLASS)
define(`PREFIX', `PyB'CLASS)
define(`APITYPE', `PyB'CLASS`Type')
define(`APIOBJECT', `PyB'CLASS`Object')
define(`BEAPITYPE', `B'CLASS)

static PyObject *ECLASS;

dnl Inheritance scheme for C++ classes derived from Be API for Python:
dnl  "var"  just Be API class. (Obsolete?)
dnl  "ref"  add 4-byte tag to identify Python-internal objects, & ptr.
dnl         "VFUNS"  has virtual functions, from Python instance wrapper.
dnl                  "handler"  not "looper", but has Looper() function.
dnl                  "looper"   has its own Python thread.
dnl                             "BApplication" special looper.
dnl
dnl  "var" vs. "ref" basically revolves around the FromIt function
dnl  (e.g., PyBHandler_FromBHandler() - this function gets a pointer
dnl  to a C object and wraps it up in a Python C object.)  It might
dnl  copy the C object, which would be the normal case ("var"), but
dnl  many C objects wouldn't take well to that - a BLooper, for example,
dnl  so we'll want a Python reference to that very C object.  In this
dnl  case, Python just needs to know that it should only delete the
dnl  C object, when it created it.  This distinction is recorded in
dnl  the C object (because that's what FromIt gets), along with a pointer
dnl  back to the Python C object.  When the stamp is recognized, FromIt
dnl  returns the same Python C object.  For an example - the DispatchMessage
dnl  virtual hook gets a BHandler, and needs to convert that to a PyBHandler
dnl  for its Python function.  Since the system accepts external objects,
dnl  not created here, we may point to either our derived class, or the
dnl  plain Be base class, and use a variety of hacks to distinguish.
dnl
dnl  Support for virtual functions adds a table for callbacks into the
dnl  Python class instance wrapper, and thread interfaces.  The derived
dnl  class for this instantiates each supported virtual function, and
dnl  if it's not actually provided in the wrapper, calls the base class
dnl  function and returns.
dnl
dnl  These callbacks need to be integrated with Python threads.  The
dnl  model for that here is one thread per looper, and all callbacks
dnl  use their looper's thread (objects that are not themselves loopers
dnl  can call Looper() to get the thread looper.)  This model leaves
dnl  a few things out, e.g., BFilePanel/BRefFilter callbacks aren't
dnl  looking like they're going to work out at this point.  A few hook
dnl  functions get BView etc. parameters that can be used to find the
dnl  thread looper (see "looperhandler" in .dx files), but we need either
dnl  this or Handler/Looper parentage; otherwise, can't find thread state,
dnl  can't branch into Python.
dnl
dnl  Meanwhile, the Python object also has base class issues, because
dnl  a BListView for example needs to be accepted as a BView in Python
dnl  function calls just as in C++.  This happens in the AsIt function,
dnl  which goes about it in whatever funky way - once it has determined
dnl  that the object is of the BaseObject variety, via another one of
dnl  these hacky stamps.

define(`SEMANTICS', ifelse(FROMSELF, `var', `var', `ref'))
ifdef(`VFUNS',
   `ifelse(FROMSELF, `looper',
      `define(`VECLASS', `BpyLVBase')
       define(`looperspec')',
      `define(`VECLASS', `BpyHVBase')
       define(`looperspec', `$1')
       ifelse(FROMSELF, `handler',, `define(`looperless')')'
    )',
   `define(`VECLASS', `BpyBase')'
)

ifelse(FROMSELF, `abstract',
`define(`BCLASS', B`'CLASS)',
`define(`BCLASS', Bpy`'CLASS)

class BCLASS: public BEAPITYPE, public VECLASS {
	ifdef(`VFUNS', `PyObject *vfn[NVFN];')
    public:
	dnl  Constructor(s):
	percomlist(CTORDCL)
ifdef(`VFUNS', `
	~`'BCLASS`'() {
                ifdef(`looperless',`//') getPyThread(looperspec(`Looper()'));
                unbindInstance();
                unbindSelf();
                ifdef(`looperless',`//') releasePyThread(looperspec(`Looper()'));
	}
	int bindInstance(PyInstanceObject *);
	void bindType(PyObject *);
	PyObject *lookup(int i) {
		if (instance && i < NVFN)
			return vfn[i];
		else
			return 0;
	}
	list(VFNDCL)
')
};')

ifdef(`VFUNS', `
static struct vfnLookupTbl stdvfn[NVFN] = {
	vfms(VFUNS)
};
//  Set up Python/C++ peer (shadow?)
int
BCLASS::bindInstance(PyInstanceObject *inst)
{
	int count;
	ifelse(FROMSELF, `looper', `struct vfnLookupTbl lcfun = { 0, "lastchance" };
	count = VFNInventory(inst, &lastchancefun, &lcfun, 1);
	if (count < 0)
		return 0;', `count = 0;')
	count += VFNInventory(inst, vfn, stdvfn, NVFN);
	// if (count > 0)
	Py_INCREF(inst);
	return 1;
}

//  Set up Python subclass of C++ type. 

static PyObject *
searchself(PyObject *obj, char *name)
{
	PyObject *fun = PyObject_GetAttrString(obj, name);
	if (fun) {
		if (!PyMethod_Check(fun))
			fun = 0;
	} else
		PyErr_Clear();
	return fun;
}

void
BCLASS::bindType(PyObject *inst)
{
	ifelse(FROMSELF, `looper', `lastchancefun = searchself(inst, "lastchance");')
	instance = (PyInstanceObject *) inst; // Bleah!
	int i;
	for (i = 0; i < NVFN; ++i)
		vfn[stdvfn[i].index] = searchself(inst, stdvfn[i].name);
}
')

dnl  Global variables that are unstable, in the sense that their values
dnl  vary during program execution.  In the case of be_bold_font et al.,
dnl  they are null until the BApplication constructor, which normally
dnl  would tend to occur after module imports.  The C/Python object for
dnl  be_bold_font always refers to the present C value, thanks to this
dnl  function and the run-time redirection that invokes it.

ifelse(CLASS, `Font', `define(`UNSTABLE_PRESETS', `dummy')')

ifdef(`UNSTABLE_PRESETS', `decldummypresets(11, PRESET)
static void *
realfromdummy(void *was)
{
	realpresets(`', was, PRESET)
	if (!was)
		PyErr_SetString(PyExc_ValueError, "APINAME global object referenced prior to Application constructor");
	return was;
}
')

ifelse(FROMSELF, `looper',
`typedef LooperBaseObject PCLASS;',
`typedef BaseObject PCLASS;')

ifelse(FROMSELF, `looper',
`ifelse(CLASS, `Application',
`static void
PREFIX`'_dealloc(PCLASS *self)
{
}',

`static int
deleteThread(PyThreadState *tstate)
{
	PyThreadState_Clear(tstate);
	PyThreadState_Delete(tstate);
	return 1;
}

static void
PREFIX`'_dealloc(PCLASS *self)
{
	BCLASS *cobj;
	if (INTERNAL_BEPTR(self))
		cobj = (BCLASS *) self->bevoid;
	else
		cobj = 0;
	if (cobj)
		cobj->instance = 0;
	if (cobj && cobj->pystamp == BPYSTAMP) {
		cobj->pystamp = 0;
		PyThreadState *tstate = self->tstate;
		if (cobj && !self->sysref) {
			if (cobj->Lock())
				cobj->Quit();  // == delete cobj.
		}
		if (tstate) {
			//  End of the road for this thread.
			//  Would like to delete its state table.
			//  Cannot do this from same thread(?), but
			//  a pending call is OK.
			PyThreadState *cur = PyThreadState_Get();
			if (cur == tstate)
				Py_AddPendingCall(
					(int (*)(void *)) deleteThread,
					(void *) tstate);
			else
				deleteThread(tstate);
		}
	}
	self->bevoidness = 0;
	self->ob_type->tp_free((PyObject *) self);
}')',
`ifelse(FROMSELF, `abstract',`',
`static void
PREFIX`'_dealloc(PCLASS *self)
{
	if (INTERNAL_BEPTR(self)) {
	    ifelse(FROMSELF,`abstract',`BEAPITYPE *cobj = (BEAPITYPE *) self->bevoid;
		delete cobj;',
		`BCLASS *dobj = (BCLASS *) self->bevoid;
		if (dobj->frmpy()) {
			ifdef(`VFUNS', `dobj->instance = 0;')
			delete dobj;
		} else {
			BEAPITYPE *cobj = (BEAPITYPE *) self->bevoid;
			delete cobj;
		}')
	} ifelse(FROMSELF,`var', ` else ifdef(`UNSTABLE_PRESETS', `if (!(testpresets(`', self->bevoid, PRESET)))') {
		BEAPITYPE *cobj = (BEAPITYPE *) self->bevoid;
		delete cobj;
	}')
	self->bevoidness = 0;
	self->ob_type->tp_free((PyObject *) self);
}')')

//  cfunctions will be used to export the to/from functions, to other
//  Bxxx.so modules.

static struct BaseFunctions cfunctions;

typedef struct StringDx {
	char *ptr;
	int len;
} pstring;

typedef void *None;

typedef float ifloat;

static PyObject *
StatusError(const char *name, status_t stnum)
{
	static const char unknown[] = "(unknown)";
	char *r = strerror(stnum);
	if (!r)
		r = (char *) unknown;
	PyErr_SetObject(ECLASS, Py_BuildValue("ls", stnum, r));
	return 0;
}

static BEAPITYPE *nativePtr(PCLASS *);
ifelse(FROMSELF, `looper',
   `define(`mkDerivative', `
	BCLASS *$2;
	if (!INTERNAL_BEPTR($1)) {
		PyErr_SetString(PyExc_SystemError, "Illegal operation on external object.");
		return 0;
	}
	$2 = (BCLASS *) ($1)->bevoid;')')

dnl  macro to generate this function, only because in a very few cases
dnl  there is no need for it and a few bytes can be saved.
define(`isB', `static int
isBThing(PyObject *a)
{
dnl (is this ridiculous?  just make it a normal attribute!)
	PyTypeObject *tp = a->ob_type;
	PyObject *stamped;
	static PyObject *bebostamp = 0;
	if (!bebostamp)
		bebostamp = PyString_FromString(BEBOSTAMP);
	stamped = PyObject_GetAttr(a, bebostamp);
	if (stamped)
		Py_DECREF(stamped);
	return stamped && stamped == Py_None;
dnl	PyObject *mro = tp->tp_mro;
dnl	int i, n;
dnl	for (i = -1;;) {
dnl		++i;
dnl		if (i == 0) {
dnl			if (mro && PyTuple_Check(mro))
dnl				n = PyTuple_Size(mro);
dnl			else
dnl				return 0;
dnl		}
dnl		if (i < n)
dnl			tp = (PyTypeObject *) PyTuple_GetItem(mro, i);
dnl		else
dnl			return 0;
dnl	}
}')

dnl  Bring in a bunch of generated sections:

include(CODEINCL)
include(FUNCINCL)
ifdef(`VFUNS',
`static PyObject *
PREFIX`'_bind(PCLASS *self, PyObject *arg)
{
	BCLASS *cobj;
	if (INTERNAL_BEPTR(self))
		cobj = (BCLASS *) self->bevoid;
	else
		cobj = 0;
	if (!arg) {
		PyObject *inst;
		if (cobj && cobj->frmpy())
			inst = (PyObject *) cobj->instance;
		else
			inst = 0;
		if (!inst)
			inst = Py_None;
		Py_INCREF(inst);
		return inst;
	}
	if (!cobj || !cobj->frmpy()) {
		PyErr_SetString(PyExc_ValueError,
			"operation not supported on externally referenced object");
		return 0;
	}
	if (arg == Py_None)
		cobj->unbindInstance();
	else {
		if (!PyInstance_Check(arg)) {
			PyErr_SetString(PyExc_TypeError,
				"bind requires 1 instance argument");
			return 0;
		}
		if (!cobj->bindInstance((PyInstanceObject *) arg))
			return 0;
	}
	Py_INCREF(Py_None);
	return Py_None;
}')

static struct PyMethodDef PREFIX`'_methods[] = {
	methods(METHODS)
	ifdef(`VFUNS', `{"bind",		(PyCFunction) PREFIX`'_bind},')
	{NULL,		NULL}		/* sentinel */
};

static PyObject *
PREFIX`'_GetAttr(PyObject *obj, PyObject *nob)
{
	char *name = PyString_AsString(nob);
	if (name) {
		if (!strcmp(name, BEBOSTAMP)) {
			Py_INCREF(Py_None);
			return Py_None;
		}
		dnl  Bunch of code for the rare case of a data attribute,
		dnl  like "what".  Now that the object here may be a class
		dnl  instance that inherits the present type, it's possible
		dnl  to get here prior to any initialization - the class
		dnl  __init__() hasn't called BParent.__init__().  At this
		dnl  point, let's say no data attributes.
		PCLASS *self = (PCLASS *) obj;
		BEAPITYPE *cobj;
		if (INTERNAL_BEPTR(self)) {
			ifelse(FROMSELF,`abstract',`cobj = (BEAPITYPE *) self->bevoid;',
			`BCLASS *dobj = (BCLASS *) self->bevoid;
			if (dobj->frmpy())
				cobj = (BEAPITYPE *) dobj;
			else
				cobj = (BEAPITYPE *) self->bevoid;
			cobj = (BEAPITYPE *) dobj;')
		} else if (EXTERNAL_BEPTR(self)) {
			void *bevoid = self->bevoid;
			ifdef(`UNSTABLE_PRESETS', `bevoid = realfromdummy(bevoid);')
			cobj = (BEAPITYPE *) bevoid;
		} else
			cobj = 0;
		dnl } else {
		dnl 	PyErr_SetString(PyExc_SystemError, "Invalid object");
		dnl 	return 0;
		dnl }
		//  For internal use, to recognize Bethon modules.
		PyObject *ret;
		static char *attrs[] = {
			strings(ATTRIBUTES)
			0
		};

		if (cobj) {
		include(ATTRINCL)
		}
	}
	return PyObject_GenericGetAttr(obj, nob);
}


ifelse(FROMSELF, `abstract',,`static int PREFIX`'_init(PyObject *, PyObject *, PyObject *);')
ifelse(FROMSELF, `abstract',,`static PyObject *PREFIX`'_new(PyTypeObject *, PyObject *, PyObject *);')

static PyTypeObject APITYPE = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,			/*ob_size*/
	"MODULENAME`.'APINAME",		/*tp_name*/
	sizeof(PCLASS),	/*tp_size*/
	0,			/*tp_itemsize*/
	/* methods */
	ifelse(FROMSELF, `abstract', 0, `(destructor) PREFIX`'_dealloc'), /*tp_dealloc*/
	0,			/*tp_print*/
	0,			/*tp_getattr*/
	0,			/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
	0,				/* tp_as_number */
	0,				/* tp_as_sequence */
	0,				/* tp_as_mapping */
	0,				/* tp_hash */
	0,				/* tp_call */
	0,				/* tp_str */
	PREFIX`_GetAttr',		/* tp_getattro */
	0,				/* tp_setattro */
	0,				/* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
	0,				/* tp_doc */
	0,				/* tp_traverse */
	0,				/* tp_clear */
	0,				/* tp_richcompare */
	0,				/* tp_weaklistoffset */
	0,				/* tp_iter */
	0,				/* tp_iternext */
	PREFIX`'_methods,		/* tp_methods */
	0,				/* tp_members */
	0,				/* tp_getset */
	0,				/* tp_base */
	0,				/* tp_dict */
	0,				/* tp_descr_get */
	0,				/* tp_descr_set */
	0,				/* tp_dictoffset */
	ifelse(FROMSELF, `abstract', `0', `PREFIX`'_init'),		/* tp_init */
	PyType_GenericAlloc,		/* tp_alloc */
	ifelse(FROMSELF, `abstract', `0', `PREFIX`'_new'),		/* tp_new */
	_PyObject_Del,			/* tp_free */
};

static struct baseItem basemodules[MAXBASETYPES];

static BEAPITYPE *
nativePtr(PCLASS *self)
{
	int i;
	for (i = 0; i < MAXBASETYPES && self->base[i].name[0]; ++i) {
		if (self->base[i].type == &APITYPE) {
			void *bevoid = self->bevoid;
ifdef(`UNSTABLE_PRESETS',`			bevoid = realfromdummy(bevoid);')
			return (BEAPITYPE *) ((void *) (((long) bevoid) + self->base[i].offset));
		}
	}
	fprintf(stderr, "BEAPITYPE not found.\n");
	return 0;
}

//  Recursively call PyType_Ready() - PyType_Ready() will gag
//  if it hits a base that it hasn't initialized, so the hierarchy
//  has to be initialized ahead of time from the bottom up.

static void readyBases(PyTypeObject *);
static void
readyBases(PyTypeObject *tp)
{
	int n;
	if (tp->tp_bases && PyTuple_Check(tp->tp_bases))
		n = PyTuple_Size(tp->tp_bases);
	else
		n = 0;
	int i;
	for (i = 0; i < n; ++i)
		readyBases((PyTypeObject *) PyTuple_GetItem(tp->tp_bases, i));
	PyType_Ready(tp);
}


static void
initBases()
{
	static int initstate = 0;
	//  First of our kind?  
	if (initstate)
		return;
	memset(basemodules, 0, sizeof(basemodules));
	//  Need a non-null pointer value here, but cannot be sure
	//  that the first caller will have access to a properly
	//  constructed BCLASS.  Appears that any non-null value
	//  is as good as another, though.  If this is not true
	//  after all, we will have to put back in some code that
	//  comes back and cleans this up the first time a real
	//  BCLASS is available.
	BCLASS *derived = (BCLASS *) 0xdeadbeef;
	Base_init(basemodules, "APINAME",
		(long) ((BEAPITYPE *) derived) - (long) derived, &APITYPE);
	PyObject *tsb[MAXBASETYPES + 2];
	PyTypeObject *t;
	int basi = 0;
	bases(BASES)
	tsb[basi++] = (PyObject *) &PyBaseObject_Type;
	tsb[basi] = 0;
	PyObject *baseq = PyTuple_New(basi);
	for (basi = 0; tsb[basi]; ++basi)
		PyTuple_SetItem(baseq, basi, tsb[basi]);
	APITYPE.tp_bases = baseq;
	readyBases(&APITYPE);
	initstate = 1;
}

ifelse(FROMSELF,`abstract',,
`static PyObject *
PREFIX`'_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	PCLASS *self;
	self = (PCLASS *) (type->tp_alloc(type, 0));
	if (self) {
		self->bevoid = 0;
		self->bevoidness = 0;
		self->base = basemodules;
		ifelse(FROMSELF, `looper', `self->sysref = 0;
		self->tstate = PyThreadState_Get();')
	}
	return (PyObject *) self;
}
')

static BEAPITYPE *
PREFIX`_As'APINAME`'(PyObject *arg)
{

dnl	if (arg->ob_type != &APITYPE)
dnl		return 0;
dnl	return (BEAPITYPE *) ((APIOBJECT *) arg)->cobj;
dnl  The present object may be of Python type B`'CLASS, or of a
dnl  derived class, and it suits our purposes to accept either.
dnl  So if it appears that it is at least of the BeOS type generally,
dnl  try to cast to B`'CLASS from the universal base.  dynamic_cast
dnl  is supposed to return 0 if that is not legit with this object,
dnl  but I seem unable to get that to work by trying various things
dnl  at random.  So, I grub through the Python base list, which is
dnl  not really the ideal notion of what we want.
dnl  I mean, the question really is whether the object is acceptably
dnl  derived per the Be API, not whether we happen to have a Python
dnl  implementation of the type with the nominally required relationship.
dnl
dnl  abstract classes used to return 0 here, not sure why!

	APIOBJECT *ob = (APIOBJECT *) arg;
	if (!PyType_IsSubtype(arg->ob_type, &APITYPE)) {
		PyErr_SetString(PyExc_TypeError, arg->ob_type->tp_name);
		return 0;
	}
	BEAPITYPE *cobj;
	if (INTERNAL_BEPTR(ob)) {
		ifelse(FROMSELF,`abstract',`cobj = (BEAPITYPE *) ob->bevoid;', `BCLASS *dobj = (BCLASS *) ob->bevoid;
		if (dobj->frmpy())
			cobj = (BEAPITYPE *) dobj;
		else
			cobj = (BEAPITYPE *) ob->bevoid;')
	} else if (EXTERNAL_BEPTR(ob)) {
		void *bevoid = ob->bevoid;
		ifdef(`UNSTABLE_PRESETS', `bevoid = realfromdummy(bevoid);')
		cobj = (BEAPITYPE *) bevoid;
	} else {
		PyErr_SetString(PyExc_SystemError, "Invalid object");
		return 0;
	}
	return cobj;
}

dnl  BStatable is an abstract class, for example.
dnl  be_app_messenger is a "preset", already instantiated.

ifelse(FROMSELF,`abstract',
`static PyObject *
PREFIX`_From'APINAME`'(const BEAPITYPE *cobj, int internal)
{
	// Bogus function purely for standard cfunctions table.
	return 0;
}',FROMSELF,`var',
`static PyObject *
PREFIX`_From'APINAME`'(const BEAPITYPE *cobj, int internal)
{
	if (!cobj) {
		PyErr_SetString(PyExc_ValueError, "null pointer");
		return 0;
	}
	PCLASS *self = (PCLASS *) PREFIX`'_new(&APITYPE, 0, 0);
	if (self) {
		BEAPITYPE *copy = new BEAPITYPE`'((*(BEAPITYPE`' *) cobj));
		SETINT_BEPTR(self, copy);
		initBases();
	}
	return (PyObject *) self;
}',
`static PyObject *
PREFIX`_From'APINAME`'(BEAPITYPE *cob, int internal)
{
	if (!cob) {
		PyErr_SetString(PyExc_ValueError, "null pointer");
		return 0;
	}
ifdef(`VFUNS',
  `define(`basecast',`dynamic_cast<$1>($2)')',
  `define(`basecast',`($1) $2')')
	BpyBase *dobj;
	dobj = basecast(`BpyBase *', `cob');
	if (dobj && dobj->frmpy()) {
		PyObject *self = dobj->self();
		Py_INCREF(self);
		return self;
	} else {
		PCLASS *self = (PCLASS *) PREFIX`'_new(&APITYPE, 0, 0);
		if (self) {
			if (internal)
				SETINT_BEPTR(self, cob);
			else
				SETEXT_BEPTR(self, cob);
			initBases();
		}
		return (PyObject *) self;
	}
}')

static PyObject *module_dict;
include(GFUNCINCL)

static struct PyMethodDef MODULENAME`'_global_methods[] = {
include(GLMETHINCL)
	{NULL,		NULL}		/* sentinel */
};

#define set(s) PyDict_SetItemString(module_dict, #s, PyInt_FromLong(s))

`#'define preset(s,v) std`'PCLASS = (PCLASS *) PREFIX`'_new(&APITYPE, 0, 0); \
	SETEXT_BEPTR(std`'PCLASS, (void *) v); \
	initBases(); \
	PyDict_SetItemString(module_dict, `#'s, (PyObject *) std`'PCLASS);

extern "C" void
`init'MODULENAME`'()
{
ifdef(`PRESET',`	PCLASS *std`'PCLASS;')

	PyObject *mod = Py_InitModule("MODULENAME", MODULENAME`_global_methods');
	module_dict = PyModule_GetDict(mod);
	ECLASS = PyErr_NewException("MODULENAME.error", 0, 0);
	PyDict_SetItemString(module_dict, "error", ECLASS);
	// Force import to get base classes, really needed only if this is
	// a base class.
	initBases();
	PyDict_SetItemString(module_dict, "APINAME", (PyObject *) &APITYPE);
ifdef(`PRESET', `	ifdef(`UNSTABLE_PRESETS', `dummypresets(PRESET)', `presets(PRESET)')')
ifdef(`SYMBOLS', `	symbols(SYMBOLS)')
	cfunctions.AsIt = (void *(*)(PyObject *)) PREFIX`_As'APINAME;
	cfunctions.FromIt = (PyObject *(*)(const void *, int)) PREFIX`_From'APINAME;
	cfunctions.type = &APITYPE;
	PyDict_SetItemString(module_dict, "functions", PyCObject_FromVoidPtr(&cfunctions, 0));
include(GLSMINCL)
}
