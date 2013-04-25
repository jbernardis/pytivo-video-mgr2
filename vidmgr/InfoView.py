from hme import *
import re
from Config import screenHeight, screenWidth, infoHeight, infoWidth

regex = re.compile(r'^Title\s*(\d+)$')

metaXlate = { 'title': 'Title',
			'originalAirDate': 'Original Air Date',
			'time': 'Time',
			'duration': 'Duration',
			'description': 'Description',
			'seriesTitle': 'Series Title',
			'seriesId': 'Series ID',
			'episodeTitle': 'Episode Title',
			'episodeNumber': 'Episode Number',
			'movieYear': 'Movie Year',
			'tvRating': 'TV Rating',
			'mpaaRating': 'MPAA Rating',
			'starRating': 'Star Rating',
			'colorCode': 'Color Code',
			'showingBits': 'Showing Bits',
			'partCount': 'Part Count',
			'partIndex': 'Part Index',
			'callsign': 'Call Sign',
			'displayMajorNumber': 'Display Major Number',
			'vSeriesGenre': 'Series Genre',
			'vProgramGenre': 'Program Genre',
			'vChoreographer': 'Choreographer',
			'vExecProducer': 'Exec Producer',
			'vGuestStar': 'Guest Star',
			'vHost': 'Host',
			'vProducer': 'Producer',
			'vDirector': 'Director',
			'vActor': 'Actor',
			'vWriter': 'Writer',
			'__fileName': 'File Name',
			'__filePath': 'File Path',
			'alpha' : 'Alphabetical',
			}

infoLabelPercent = 30
infoRightMargin = 20

def metaTranslate(meta):
	if meta in metaXlate:
		return metaXlate[meta]
	else:
		return meta

class InfoView(View):
	def __init__(self, app, opts, font):
		xpos = (screenWidth-infoWidth)/2
		ypos = (screenHeight-infoHeight)/2

		View.__init__(self, app, width=infoWidth, height=infoHeight, xpos=xpos, ypos=ypos, visible=False)
		self.set_resource(app.myimages.Info)
		self.opts = opts
		self.labelView = []
		self.dataView = []
		self.linesPerPage = 0
		self.displayOffset = 0
		self.font = font
		self.app = app
		self.hide()
		
	def setinfogeometry(self, fontinfo):
		self.fi = fontinfo
		self.lineHeight = int(fontinfo.height)
		self.linesPerPage = 0
		lblwidth = int(infoWidth * infoLabelPercent / 100.0)
		self.datawidth = int(infoWidth * (100.0-infoLabelPercent) / 100.0) - infoRightMargin
		y = 10
		while (y + self.lineHeight <= infoHeight - 2):
			lbl = View(self.app, parent=self, width=lblwidth, height=self.lineHeight, xpos=10, ypos=y)
			data = View(self.app, parent=self, width=self.datawidth, height=self.lineHeight, xpos=10+lblwidth, ypos=y)
			self.labelView.append(lbl)
			self.dataView.append(data)
			y = y + self.lineHeight
			self.linesPerPage = self.linesPerPage + 1
			
		self.vwUp = View(self.app, parent=self, width=32, height=16, xpos=lblwidth-24, ypos=2)
		self.vwUp.set_resource(self.app.myimages.InfoUp)
		self.vwDown = View(self.app, parent=self, width=32, height=16, xpos=lblwidth-24, ypos=self.height-18)
		self.vwDown.set_resource(self.app.myimages.InfoDown)

		self.clear()
	
	def show(self):
		self.clear_resource()
		self.set_resource(self.app.myimages.Info)
		self.isVisible = True
		self.set_visible(True)
		
	def hide(self):
		self.isVisible = False
		self.set_visible(False)
		
	def clear(self):
		self.dataContent = []
		self.labelContent = []
		self.lineCount = 0;
		self.displayOffset = 0;
		
	def addline(self, label, data):
		if label in metaXlate:
			lbl = metaXlate[label]
		else:
			lbl = label
	
		if type(data) is list:
			dstring = ', '.join(data)
		else:
			dstring = data
			
		if label in self.opts['metaspacebefore'] and not self.lastLineBlank:
			self.labelContent.append("")
			self.dataContent.append("")
			self.lineCount = self.lineCount + 1

		spacewidth = self.measure(" ")
		newstring = ""
		nslength = 0
		for w in dstring.split(' '):
			wlen = self.measure(w)
			if nslength != 0:
				wslen = wlen + spacewidth
			else:
				wslen = wlen
			if (nslength + wslen) < self.datawidth:
				if nslength != 0:
					newstring = newstring + " "
				newstring = newstring + w
				nslength = nslength + wslen
			else:
				self.labelContent.append(lbl)
				self.dataContent.append(newstring)
				self.lineCount = self.lineCount + 1
				self.lastLineBlank = False
				newstring = w
				nslength = wlen
				lbl = ""
		if nslength != 0:
			self.labelContent.append(lbl)
			self.dataContent.append(newstring)
			self.lineCount = self.lineCount + 1
			self.lastLineBlank = False
			
		if label in self.opts['metaspaceafter']:
			self.labelContent.append("")
			self.dataContent.append("")
			self.lineCount = self.lineCount + 1
			self.lastLineBlank = True
		
	def measure(self, string):
		if len(string) == 0: return(0)
		
		fi = self.fi
		width = 0
		for c in string:
			info = fi.glyphs.get(c, (0, 0))
			width += info[0]	# advance
		if info[1] > info[0]:   # bounding
			width += (info[1] - info[0])
		return int(width)

	def loadmetadata(self, meta):
		def cmpTitle(a, b):
			xa = regex.search(a)
			xb = regex.search(b)
			if xa and xb:
				return cmp(int(xa.group(1)), int(xb.group(1)))
			else:
				if a in metaXlate:
					sa = metaXlate[a]
				else:
					sa = a
				if b in metaXlate:
					sb = metaXlate[b]
				else:
					sb = b

				return cmp(sa, sb)

		self.clear()
		self.lastLineBlank = True
		if meta == None: return
		
		for m in self.opts['metafirst']:
			if m in meta:
				self.addline(m, meta[m])

		skeys = sorted(meta.keys(), cmpTitle)
		for m in skeys:
			if m not in self.opts['metafirst'] and m not in self.opts['metaignore']:
				self.addline(m, meta[m])
		
	def paint(self):
		if self.displayOffset == 0:
			self.vwUp.set_visible(False)
		else:
			self.vwUp.set_visible(True)
			
		if self.displayOffset + self.linesPerPage >= self.lineCount:
			self.vwDown.set_visible(False)
		else:
			self.vwDown.set_visible(True)
			
		i = 0
		while i < self.linesPerPage:
			n = self.displayOffset + i
			if n >= self.lineCount:
				self.labelView[i].set_text("")
				self.dataView[i].set_text("")
			else:
				self.labelView[i].set_text(self.labelContent[n],
					font=self.font,
					colornum=0xffffff,
					flags=RSRC_HALIGN_LEFT)
				self.dataView[i].set_text(self.dataContent[n],
					font=self.font,
					colornum=0xffffff,
					flags=RSRC_HALIGN_LEFT)
			i = i + 1
	
	def pagedown(self):
		if self.displayOffset + self.linesPerPage >= self.lineCount:
			return False
		
		self.displayOffset = self.displayOffset + self.linesPerPage
		if self.displayOffset + self.linesPerPage > self.lineCount:
			self.displayOffset = self.lineCount - self.linesPerPage
		self.paint()
		return True
	
	def pageup(self):
		if self.displayOffset == 0:
			return False;
		
		self.displayOffset = self.displayOffset - self.linesPerPage
		if self.displayOffset < 0:
			self.displayOffset = 0
		self.paint()
		return True
		

