#
#  To do, maybe:
#  - Automatically insert slack cells, like between two visible cells.
#  - Automatically insert chock cells, between visibles and at edges.
#  - Resize function to call from FrameResized().
#

__doc__ = """
Row and column layout system.

Four kinds of cells, each with a horizontal and vertical class, so
for example Chock is really HChock and VChock.

    Chock:   a space of fixed size
    Slack:   a space with initial size and a weighted ability to grow.
    Rack:    a BView container that imposes its own dimension.
    Row:     a sequence of cells (either horizontal or vertical!)
"""

class Rack:
	"""
[HV]Rack(BView, min = 0.0, max = infinity)

Imposes the specified size, overriding BView::GetPreferredSize()
(in the appropriate dimension only.)
	"""
	def __init__(self, view, min = 0.0, max = 7000.0, name = None):
		self.min = min
		self.max = max
		self.view = view
		self.name = name
	def GetPreferredSize(self):
		x, y = self.view.GetPreferredSize()
		return self.stretch(x, y)
	def ResizeTo(self, x, y):
		return self.view.ResizeTo(x, y)
	def MoveTo(self, x, y):
		return self.view.MoveTo(x, y)

class HRack(Rack):
	def stretch(self, x, y):
		if x < self.min:
			x = self.min
		elif x > self.max:
			x = self.max
		return x, y

class VRack(Rack):
	def stretch(self, x, y):
		if y < self.min:
			y = self.min
		elif y > self.max:
			y = self.max
		return x, y

class Chock:
	def __init__(self, dim):
		self.dim = dim
	def ResizeTo(self, x, y):
		pass
	def MoveTo(self, x, y):
		pass

class HChock(Chock):
	def GetPreferredSize(self):
		return self.dim, 0.0

class VChock(Chock):
	def GetPreferredSize(self):
		return 0.0, self.dim

class Slack:
	def __init__(self, min = 4.0, max = 7000.0, weight = 0.0, name = None):
		self.name = name
		self.min = min
		self.max = max
		self.slackweight = weight

class HSlack(Slack):
	def size(self):
		return self.min, 0.0
	def inflate(self, oldsize, slack, normal):
		# if normal <= 0.0 or slack <= 0.0:
		if normal <= 0.0 or slack == 0.0:
			return oldsize
		ox, oy = oldsize
		dx = slack * self.slackweight / normal
		if self.name:
			print self.name, oldsize, slack, '*', self.slackweight, '/', normal, '=', dx
		return ox + dx, oy

class VSlack(Slack):
	def size(self):
		return 0.0, self.min
	def inflate(self, oldsize, slack, normal):
		# if normal <= 0.0 or slack <= 0.0:
		# if normal <= 0.0 or slack == 0.0:
		# 	return oldsize
		ox, oy = oldsize
		dy = slack * self.slackweight / normal
		if self.name:
			print self.name, oldsize, slack, '*', self.slackweight, '/', normal, '=', dy
		return ox, oy + dy

class Row:
	"""
[HV]Row([box, ...])
	"""
	def __init__(self, boxes, name = None):
		self.boxes = boxes
		self.slack = 0.0
		self.name = name
	def size(self):
		dl = []
		for box in self.boxes:
			try:
				sz = box.size()
			except AttributeError:
				sz = box.GetPreferredSize()
			dl.append(sz)
		self.sz = dl
		return self.sum()
	def layout(self, x, y, pbound):
		#  Inventory slack weights.
		if self.name:
			print 'layout', self.name, x, y, pbound
		self.setbound(pbound)
		# print pbound, 'layout slack', self.slack, self.bound
		iw = 0.0
		for box in self.boxes:
			try:
				iw = iw + box.slackweight
			except AttributeError:
				pass

		#  Set final sizes and positions.
		for i in range(len(self.boxes)):
			dx, dy = self.sz[i]
			box = self.boxes[i]
			try:
				dx, dy = box.inflate((dx, dy), self.slack, iw)
				self.sz[i] = (dx, dy)
			except AttributeError:
				# (no inflate function)
				try:
					box.layout(x, y, self.rowbound(dx, dy)) 
				except AttributeError:
					# (no layout function)
					box.ResizeTo(dx, dy)
					box.MoveTo(x, y)
			x, y = self.move(i, x, y, dx, dy)
		if self.name:
			print self.name, self.sz

class HRow(Row):
	def sum(self):
		x = 0.0
		y = 0.0
		for dx, dy in self.sz:
			x = x + dx
			if y < dy:
				y = dy
		self.bound = (x, y)
		return x, y
	def setbound(self, bound):
		self.slack = bound[0] - self.bound[0]
		self.bound = bound
	def rowbound(self, dx, dy):
		return dx, self.bound[1]
	def move(self, i, x, y, dx, dy):
		x = x + dx
		return x, y

class VRow(Row):
	def sum(self):
		x = 0.0
		y = 0.0
		for dx, dy in self.sz:
			if x < dx:
				x = dx
			y = y + dy
		self.bound = (x, y)
		return x, y
	def setbound(self, bound):
		self.slack = bound[1] - self.bound[1]
		self.bound = bound
	def rowbound(self, dx, dy):
		return self.bound[0], dy
	def move(self, i, x, y, dx, dy):
		y = y + dy
		return x, y

class HCenter(HRow):
	def __init__(self, view, min = 0.0, max = 7000.0, grav = 0.5,
			name = None):
		boxes = [
			HSlack(min = min, max = max, weight = grav/1.0),
			view,
			HSlack(min = min, max = max, weight = (1.0 - grav)/1.0)
		]
		HRow.__init__(self, boxes)

class VCenter(VRow):
	def __init__(self, view, min = 0.0, max = 7000.0, grav = 0.5,
			name = None):
		if name:
			topname = 'top-' + name
			bottomname = 'bottom-' + name
		else:
			topname = None
			bottomname = None
		boxes = [
			VSlack(min = min, max = max, weight = grav/1.0,
				name = topname),
			view,
			VSlack(min = min, max = max, weight = (1.0 - grav)/1.0,
				name = bottomname)
		]
		VRow.__init__(self, boxes, name)
