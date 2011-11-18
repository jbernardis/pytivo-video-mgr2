'''
Created on Aug 3, 2011

@author: Jeff
'''

import os
from Config import TYPE_VIDDIR
from Node import cmpList

class VideoDir:
	def __init__(self, opts, name, rpath, apath, share):
		self.opts = opts.copy()
		self.name = name
		self.share = share
		self.path = rpath
		self.apath = apath
		self.title = name
		self.videoList = []
		self.dirList = []
		self.meta = {}
		
	def getObjType(self):
		return TYPE_VIDDIR
		
	def formatDisplayText(self, fmt):
		return "%s (%d)" % (self.title, self.__len__())
	
	def getFullTitle(self):
		return "%s : %s" % (self.share, os.path.join(self.path, self.name))
		
	def formatSortText(self, fmt):
		return self.name
	
	def getShare(self):
		return self.share
	
	def getName(self):
		return self.name
	
	def getPath(self):
		return self.path
	
	def getFullPath(self):
		return os.path.join(self.apath, self.name)
	
	def setMeta(self, meta):
		self.meta = meta
		
	def getMeta(self):
		return self.meta
	
	def setOpts(self, opts):
		self.opts = opts.copy()
		
	def getOpts(self):
		return self.opts
		
	def addVideo(self, v):
		self.videoList.append(v)	
		v.addVideoRef(self)
				
	def delVideo(self, vf):
		for i in range(len(self.videoList)):
			if vf == self.videoList[i]:
				del self.videoList[i]
				return
			
	def setVideoList(self, vl):
		self.videoList = [n for n in vl]
		
	def getVideoList(self):
		return self.videoList
				
	def addDir(self, d):
		self.dirList.append(d)

	def setDirList(self, dl):
		self.dirList = [n for n in dl]
		
	def getDirList(self):
		return self.dirList				

	def sort(self):
		def cmpNodes(a, b):
			ta = a.formatSortText(self.opts['sortopt'])
			tb = b.formatSortText(self.opts['sortopt'])
			if (self.opts['sortup']):
				return cmpList(ta, tb)
			else:
				return cmpList(tb, ta)
		
		s = sorted(self.videoList, cmpNodes)
		self.videoList = s
		s = sorted(self.dirList, cmpNodes)
		self.dirList = s
		
	def __iter__(self):
		self.__dindex__ = 0
		self.__vindex__ = 0
		return (self)

	def next(self):
		if self.__dindex__ < len(self.dirList):
			i = self.__dindex__
			self.__dindex__ += 1
			return self.dirList[i]

		if self.__vindex__ < len(self.videoList):
			i = self.__vindex__
			self.__vindex__ += 1
			return self.videoList[i]

		raise StopIteration
	
	def getItem(self, x):
		if x < len(self.dirList):
			return self.dirList[x]
		
		lx = x - len(self.dirList)
		if lx < len(self.videoList):
			return self.videoList[lx]
		
		return None
	
	def __len__(self):
		return len(self.dirList) + len(self.videoList)
		
	def __str__(self):
		
		s1 = "Videos: " 
		for vl in self.videoList:
			s1 += vl.filename + ' '
		s1 += "\n"
		
		s2 = "Dirs: "
		for d in self.dirList:
			s2 += str(d)
		s2 += "\n"
		return self.root + ":\n" + s1 + s2
