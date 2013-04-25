from hme import *
from VideoDir import VideoDir
from DVDDir import DVDDir
from VideoFile import VideoFile
import os

from Config import ( detailViewXPos, detailViewWidth, detailDescHeight,
					detailDescWidth, detailDescXPos, detailDescYPos,
					thumbnailwidth, thumbnailheight, thumbnailxpos, thumbnailypos, artworkDir,
					TYPE_VIDFILE, TYPE_DVDDIR, TYPE_VIDDIR, TYPE_NODE, TYPE_VIDSHARE, TYPE_DVDSHARE )

AppPath = os.path.dirname(__file__)

class DetailDisplayManager:
	def __init__(self, app, opts, tc):
		self.app = app
		self.opts = opts
		self.tc = tc
		self.imagemap = {}
		
		self.vwDetail = View(self.app, width=detailViewWidth, xpos = detailViewXPos)
		self.vwDetailDescription = View(self.app, height=detailDescHeight, width=detailDescWidth,
									ypos=detailDescYPos, xpos=detailDescXPos, parent=self.vwDetail)
		self.vwDetailThumb = View(self.app, width=thumbnailwidth, height=thumbnailheight, xpos=thumbnailxpos, ypos=thumbnailypos, parent=self.vwDetail)
		
				
	def cleanup(self):
		return
	
	def show(self, item):
		if item == None:
			self.vwDetailDescription.set_text("")
			self.vwDetailThumb.clear_resource()
			return
		
		meta = item.getMeta()
		if 'description' in meta:
			self.vwDetailDescription.set_text(meta['description'], font=self.app.myfonts.descfont,
						colornum=0xffffff,
						flags=RSRC_TEXT_WRAP + RSRC_HALIGN_LEFT + RSRC_VALIGN_TOP)
		else:
			self.vwDetailDescription.set_text("")
			
		otype = item.getObjType()
		if otype == TYPE_VIDFILE:
			p = item.getPath()
			fn = item.getFileName()
			mapkey = p + ':' + fn
			if mapkey in self.imagemap:
				thumb = self.imagemap[mapkey]
			else:
				thumb = self.getThumb(p, fn, item.isDVDVideo())
				if thumb:
					self.imagemap[mapkey] = thumb
					
			if thumb:
				self.vwDetailThumb.set_resource(thumb, flags=RSRC_VALIGN_TOP+self.opts['thumbjustify'])
			else:
				self.vwDetailThumb.clear_resource()
				
		elif otype in [TYPE_VIDDIR, TYPE_DVDDIR]:
			mapkey = item.getFullPath()
			if mapkey in self.imagemap:
				thumb = self.imagemap[mapkey]
			else:
				thumb = self.getDirThumb(mapkey, otype == TYPE_DVDDIR)
				if thumb:
					self.imagemap[mapkey] = thumb
					
			if thumb:
				self.vwDetailThumb.set_resource(thumb, flags=RSRC_VALIGN_TOP+self.opts['thumbjustify'])
			else:
				self.vwDetailThumb.clear_resource()
		elif otype in [TYPE_NODE]:
			mapkey = os.path.join(AppPath, artworkDir, item.getPath()+".jpg")
			if mapkey in self.imagemap:
				thumb = self.imagemap[mapkey]
			else:
				thumb = self.getShareThumb(mapkey)
				if thumb:
					self.imagemap[mapkey] = thumb
					
			if thumb:
				self.vwDetailThumb.set_resource(thumb, flags=RSRC_VALIGN_TOP+self.opts['thumbjustify'])
			else:
				self.vwDetailThumb.clear_resource()
		
		elif otype in [TYPE_VIDSHARE, TYPE_DVDSHARE]:
			mapkey = os.path.join(item.getRoot(), "share.jpg")
			if mapkey in self.imagemap:
				thumb = self.imagemap[mapkey]
			else:
				thumb = self.getShareThumb(mapkey)
				if thumb:
					self.imagemap[mapkey] = thumb
					
			if thumb:
				self.vwDetailThumb.set_resource(thumb, flags=RSRC_VALIGN_TOP+self.opts['thumbjustify'])
			else:
				self.vwDetailThumb.clear_resource()
		
		else:
			self.vwDetailThumb.clear_resource()

	def getThumb(self, dir, name, isDVD):
		thumb = None
		names = []
		names.append(os.path.join(dir, name + '.jpg'))
		names.append(os.path.join(dir, '.meta', name + '.jpg'))
		names.append(os.path.join(dir, self.opts['thumbfolderfn']))
		names.append(os.path.join(dir, '.meta', self.opts['thumbfolderfn']))
		if isDVD: 
			names.append(os.path.join(dir, 'default.jpg'))
			names.append(os.path.join(dir, '.meta', 'default.jpg'))
			
		for tfn in names:
			data = self.tc.getImageData(tfn)
			if data:
				thumb = Image(self.app, tfn, data=data)
				break
			
		return thumb
	
	def getDirThumb(self, dir, isDVD):
		thumb = None
		names = []
		names.append(os.path.join(dir, self.opts['thumbfolderfn']))
		names.append(os.path.join(dir, '.meta', self.opts['thumbfolderfn']))
		if isDVD: 
			names.append(os.path.join(dir, 'default.jpg'))
			names.append(os.path.join(dir, '.meta', 'default.jpg'))
			
		for tfn in names:
			data = self.tc.getImageData(tfn)
			if data:
				thumb = Image(self.app, tfn, data=data)
				break
			
		return thumb
	
	def getShareThumb(self, fn):
		thumb = None
			
		data = self.tc.getImageData(fn)
		if data:
			thumb = Image(self.app, fn, data=data)
			
		return thumb
