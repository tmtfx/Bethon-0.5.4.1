#  Copyright 1999 by Donn Cave, Seattle, Washington, USA.
#  All rights reserved.  Permission to copy, modify and distribute this
#  material is hereby granted, without fee, provided that the above
#  copyright notice appear in all copies.

import BRoster
import bstructs

def find(app):
	be_roster = BRoster.be_roster
	for a in be_roster.GetAppList():
		try:
			z = be_roster.GetRunningAppInfo(a)
			z = bstructs.app_info(z)
			if z.ref.name == app:
				return z
		except BRoster.error, val:
			pass
