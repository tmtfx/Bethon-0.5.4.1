#ifndef __BPYBASE_H_
#define __BPYBASE_H_

#include <app/Looper.h>

#include "Python.h"

#define BPYSTAMP 0xc2d0d9c2

class BpyBase {
public:
	uint32 pystamp;
	PyObject *pyself;
	BpyBase() { pystamp = BPYSTAMP; pyself = 0; }
	~BpyBase() {
		unbindSelf();
		pystamp = 0;
	}
	bool frmpy() { return pystamp == BPYSTAMP; }
	PyObject *self() { return pyself; }
	void bindSelf(PyObject *self) {
		pyself = self;
		// Py_INCREF(pyself);
	}
	void unbindSelf() {
		if (pyself) {
			// Py_DECREF(pyself);
			pyself = 0;
		}
	}
};

struct vfnLookupTbl {
    int index;
    char *name;
};

class BpyVBase: public BpyBase {
public:
	PyInstanceObject *instance;
	BpyVBase(): BpyBase() { instance = 0; }
	~BpyVBase() { unbindInstance(); }
	virtual int bindInstance(PyInstanceObject *) = 0;
	void unbindInstance() {
		//  Think this is OK without thread lock.
		if (instance) {
			pystamp = 0;
			Py_DECREF(instance);
			instance = 0;
		}
	}
	virtual PyObject *lookup(int) = 0;
	int VFNInventory(PyInstanceObject *, PyObject **, struct vfnLookupTbl *, int);
};

class BpyLVBase: public BpyVBase {
	PyThreadState *loopthread;
public:
	PyObject *lastchancefun;
	BpyLVBase(): BpyVBase() {
		loopthread = 0;
		lastchancefun = 0;
	}
	~BpyLVBase() {
		getPyThread();
		unbindInstance();
		unbindSelf();
		releasePyThread();
	}
	int getPyThread() {
		if (loopthread)
			PyEval_AcquireThread(loopthread);
		return 1;
	}
	void initPyThread(PyThreadState *tstate) {
		loopthread = tstate;
	}
	void releasePyThread() {
		if (loopthread)
			PyEval_ReleaseThread(loopthread);
	}
	void lastchance() {
		if (lastchancefun) {
			PyObject *t, *v, *tb;
			PyErr_Fetch(&t, &v, &tb);
			PyObject *args = 0;
			if (t && v && tb)
				args = PyTuple_New(3);
			if (args) {
				PyTuple_SetItem(args, 0, t);
				PyTuple_SetItem(args, 1, v);
				PyTuple_SetItem(args, 2, tb);
			}
			PyObject *res = PyEval_CallObject(lastchancefun, args);
			if (args)
				Py_DECREF(args);
			if (res) {
				Py_DECREF(res);
				return;
			}
		}
		PyErr_Print();
	}
};

class BpyHVBase: public BpyVBase {
public:
	BpyHVBase(): BpyVBase() {};
	int getPyThread(BLooper *looper) {
		if (looper) {
			BpyLVBase *b = dynamic_cast<BpyLVBase *>(looper);
			if (b)
				return b->getPyThread();
			else
				return 0;
		} else
			return 0;
	}
	void releasePyThread(BLooper *looper) {
		if (looper) {
			BpyLVBase *b = dynamic_cast<BpyLVBase *>(looper);
			if (b)
				b->releasePyThread();
		}
	}
	void lastchance(BLooper *looper) {
		if (looper) {
			BpyLVBase *b = dynamic_cast<BpyLVBase *>(looper);
			if (b)
				b->lastchance();
		}
	}
};


//  All classes also implement this function, but separately since it refers
//  different vfn tables.
//  PyObject *lookup(int i) {
// 	if (instance && i < NVFN)
// 		return vfn[i];
// 	else
// 		return 0;
//  }

#endif
