dnl  Copyright 1999 by Donn Cave, Seattle, Washington, USA.
dnl  All rights reserved.  Permission to copy, modify and distribute this
dnl  material is hereby granted, without fee, provided that the above
dnl  copyright notice appear in all copies.

define(`list',
`ifelse($1,, ,$1
`	list(shift($*))')')
define(`percomlist',
`ifelse($1,, ,`translit($1,`.',`,')'
`	percomlist(shift($*))')')

define(`includes',
`ifelse($1,, ,#include $1
`includes(shift($*))')')

define(`strings',
`ifelse($1,, ,"$1"`,'
`	strings(shift($*))')')

dnl define(`bases',
dnl `ifelse($1,, ,"B$1"`,'
dnl `	bases(shift($*))')')
dnldefine(`bases',
dnl`ifelse($1,, ,{"B$1"`,' (long)((B$1 *) zob) - (long) zob}`,'
dnl`	bases(shift($*))')')
define(`bases',
`ifelse($1,, ,t = Base_initFromName`('basemodules`,' "B$1"`,' (long) ((B$1 *) derived) - (long) derived`)';
	`if (t && basi < MAXBASETYPES)
		tsb[basi++] = (PyObject *) t;'
`	bases(shift($*))')')
define(`debases',
`ifelse($1,, ,Base_initFromName`('basemodules`,' "B$1"`,' 0`)';
`	debases(shift($*))')')

define(`symbols',
`ifelse($1,, ,set($1);
`	symbols(shift($*))')')

define(`presets',
`ifelse($1,, ,preset($1, $2);
`	presets(shift(shift($*)))')')
define(`dummypresets',
`ifelse($1,, ,preset($1, dummy_$2);
`	dummypresets(shift(shift($*)))')')
define(`decldummypresets',
`ifelse($2,, ,static void *dummy_$2 = (void *) $1;
`decldummypresets(incr($1), shift(shift(shift($*))))')')
define(`testpresets',
`ifelse($3,, ,$1 $2 == dummy_`'$3
`	testpresets(`||', $2, shift(shift(shift(shift($*)))))')')
define(`realpresets',
`ifelse($3,, ,$1 if ($2 == dummy_$3)
		$2 = (void *) $4;
`	realpresets(`else', $2, shift(shift(shift(shift($*)))))')')

define(`methods',
`ifelse($1,, ,{"$1"`, (PyCFunction) PyB'CLASS`'_$1`, 1, (char *) PyB'CLASS`'_$1`_doc},'
`	methods(shift($*))')')

define(`exptbl',
`ifelse($1,, ,cfunctions.$1 = PyB`'CLASS`'_$1;
`	exptbl(shift($*))')')

dnl define(`imports',
dnl `ifelse($1,, ,#include "$1.h"
dnl static struct $1`'Functions *$1`'CTbl = 0;
dnl `imports(shift($*))')')
define(`imports',
`ifelse($1,, ,static struct BaseFunctions *$1`'CTbl = 0;
`imports(shift($*))')')
dnl define(`imports',
dnl `ifelse($1,, ,`#'ifndef $1`'_CTBL_
dnl `#'define $1`'_CTBL_
dnl static struct BaseFunctions *$1`'CTbl = 0;
dnl `#'endif
dnl `imports(shift($*))')')

define(`append', `define(`$1', defn(`$1')`,$2')')

define(`vhincl',
`ifelse($1,, ,#include "$1.h"
`vhincl(shift($*))')')

define(`vdincl',
`ifelse($1,, ,#include "$1.def"
`vdincl(shift($*))')')

define(`venums', `ifelse($1,, ,`v'$1`,' `venums(shift($*))')')

define(`vfns',
`ifelse($1,, ,$1`'VFNs
`	vfns(shift($*))')')

dnl define(`vfms',
dnl `ifelse($1,, ,$1`'VFMs
dnl `	vfms(shift($*))')')

define(`vfms',
`ifelse($1,, ,`{v'$1`, "'$1`"},'
`	vfms(shift($*))')')

define(`BCLASS', `B'CLASS)
define(`PCLASS', `PyB'CLASS`Object')
define(`ECLASS', `PyB'CLASS`Error')
dnl define(`upper', `translit($1,`abcdefghijklmnopqrstuvxyz', `ABCDEFGHIJKLMNOPQRSTUVXYZ')')

define(`acount', `ifelse($1,,`0',`incr(acount(shift($*)))')')
