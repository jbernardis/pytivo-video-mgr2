'''
Created on Aug 3, 2011
'''
import os

from DVDDir import DVDDir
from Config import TYPE_VIDFILE, TYPE_DVDDIR
from Node import SORTSEP

def stripArticle(string):
	lstring = string.lower()
	result = string
	
	for article in [ 'the ', 'an ', 'a ']:
		if lstring.startswith(article):
			result = string[len(article):].lstrip()
			break
		
	return result

class VideoFile:
	def __init__(self, opts, dir, fn, fid):
		self.opts = opts.copy()
		self.filename = fn
		self.title = fn
		self.fileID = fid
		self.path = dir
		self.vRef = []
		self.multiLinks = False
		self.meta = {}
		self.metaRef = []
		self.index = None
		
	def getObjType(self):
		return TYPE_VIDFILE
	
	def flatten(self, index):
		self.index = index
		self.vRef = []
		self.metaRef = []

	def unflatten(self, node):
		self.index = None
		self.vRef.append(node)

	def getIndex(self):
		return self.index
	
	def getOpts(self):
		return self.opts

	def addVideoRef(self, dn, path, fn):
		if path != None and fn != None:
			if path != self.path or fn != self.filename:
				self.multiLinks = True
				
		self.vRef.append(dn)
		
	def getFileID(self):
		return self.fileID

	def getVideoRef(self):
		return(self.vRef)

	def getRefCount(self):
		return len(self.vRef)
	
	def isDeletable(self):
		if self.isDVDVideo():
			return False

		# prevent deletes if more that one link to this file
		if self.multiLinks:
			return False

		return self.opts['deleteallowed']
	
	def isDVDVideo(self):
		for d in self.vRef:
			if d.getObjType() == TYPE_DVDDIR:
				return True

		return False
	
	def delVideo(self):
		if not self.isDeletable():
			return
		
		for d in self.vRef:
			d.delVideo(self)
			
		for m in self.metaRef:
			m.delVideo(self)
			
		self.removeFiles()
	
	def getFileName(self):
		return self.filename

	def getPath(self):
		return self.path
	
	def getFullPath(self):
		return os.path.join(self.getPath(), self.getFileName())
	
	def getMetaFileName(self):
		path = self.getPath();
		filename = self.getFileName()
		
		fn1 = os.path.join(path, '.meta', filename) + '.txt'
		if os.path.exists(fn1):
			return fn1
		
		fn2 = os.path.join(path, filename) + '.txt'
		if os.path.exists(fn2):
			return fn2

		if os.path.exists(os.path.join(path, '.meta')):
			return fn2
		else:
			return fn1		
	
	def getRelativePath(self):
		if len(self.vRef) == 0:
			return None

		return os.path.join(self.vRef[0].getPath(), self.vRef[0].getName(), self.getFileName())
	
	def getShare(self):
		for v in self.vRef:
			s = v.getShare()
			if s is not None:
				return s
			
		return None
	
	def getShareList(self):
		l = []
		if len(self.vRef) == 0:
			return l
		
		for v in self.vRef:
			sh = v.getShare()
			if sh:
				l.append(sh)
		
		return l;
	
	def setMeta(self, meta):
		self.meta = meta
		self.meta['__fileName'] = self.getFileName()
		self.meta['__filePath'] = self.getPath()
		self.formatDisplayText(self.opts['dispopt'])
		
	def setMetaItem(self, key, value):
		if key.startswith('v'):
			if key in self.meta:
				if value not in self.meta[key]:
					self.meta[key].append(value)
			else:
				self.meta[key] = [value]
		else:
			self.meta[key] = value
		
	def formatDisplayText(self, fmt):
		result = ""

		if fmt != None:
			for f in fmt:
				if f in self.meta:
					if len(result) > 0:
						result += ' ' + self.opts['dispsep'] + ' '
					data = self.meta[f]
					if type(data) is list:
						result += ', '.join(data)
					else:
						result += data

				elif f == 'file':
					if len(result) > 0:
						result += ' ' + self.opts['dispsep'] + ' '
					result += self.getFileName()
			
		if len(result) == 0:
			if 'title' in self.meta:
				result = self.meta['title']
			else:
				result = self.getFileName()
			
		return result


	def formatSortText(self, fmt):
		result = ""
		terms = 0
		for f in fmt:
			if result != "":
				result += SORTSEP
			if f in self.meta:
				data = self.meta[f]
				if type(data) is list:
					result += ','.join(data)
				else:
					if f in [ 'title', 'episodeTitle' ] and self.opts['ignorearticle']:
						data = stripArticle(self.meta[f])
					result += data
				terms += 1
			elif f == 'file':
				result = result + self.getFileName()
				terms += 1
			elif f == 'pushDate':
				result += "1970-01-01T00:00:00Z"
				terms += 1
			
		if terms == 0:
			result = self.getFileName()

		return result
			
	def getMeta(self):
		return self.meta

	def addMetaRef(self, mr):
		self.metaRef.append(mr)
		
	def removeFiles(self):
		path = self.getPath()
		fn = self.getFileName()
		fullname = os.path.join(path, fn)
		
		for f in [ fullname,
				fullname + ".txt",
				os.path.join(path, ".meta", fn + '.txt'),
				fullname + ".jpg",
				os.path.join(path, ".meta", fn + '.jpg') ]:
			try:
				print "Attempting to delete (%s)" % f
				os.remove(f)
			except:
				print "delete failed"
					
