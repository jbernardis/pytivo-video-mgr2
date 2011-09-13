'''
Created on Aug 3, 2011

@author: Jeff
'''
import os
import sys
sys.path.append(os.path.dirname(__file__))

from VideoShare import VideoShare
from DVDShare import DVDShare
from VideoFile import VideoFile
from VideoDir import VideoDir
from Meta import MetaHarvester
from DVDDir import DVDDir
import ConfigParser
import cPickle as pickle
from Node import Node
from Config import SHARETYPE_VIDEO, SHARETYPE_DVD

VMSECTION = "vidmgr"
CACHEFILE = "video.cache"
OPTSECT = 'options'
BUILDINI = 'buildcache.ini'
NESTLIMIT = 10000

class CacheError(Exception):
	pass	

def flatten(node, vfl):
	if node == None:
		return
	
	if (isinstance(node, Node)
			or isinstance(node, VideoDir)
			or isinstance(node, DVDDir)):
		nvl = []
		for v in node.getVideoList():
			i = v.getIndex()
			if i == None:
				i = len(vfl)
				vfl.append(v)
				v.flatten(i)
				
			nvl.append(i)
			
		node.setVideoList(nvl)
		
		for v in node.getDirList():
			flatten(v, vfl)

	elif isinstance(node, DVDShare) or isinstance(node, VideoShare):
		flatten(node.getVideoDir(), vfl)

	else:
		raise CacheError("Encountered unknown object type while flattening")

def unflatten(node, vfl):
	if node == None:
		return
	
	if (isinstance(node, Node)
			or isinstance(node, VideoDir)
			or isinstance(node, DVDDir)):
		nvl = []
		for v in node.getVideoList():
			if v >= len(vfl):
				raise CacheError("Video index (%d) greater than video array size (%d)" %(v, len(vfl)))
			
			vf = vfl[v]
			vf.unflatten(node)
			nvl.append(vf)
			
		node.setVideoList(nvl)
		
		for v in node.getDirList():
			unflatten(v, vfl)

	elif isinstance(node, DVDShare) or isinstance(node, VideoShare):
		unflatten(node.getVideoDir(), vfl)

	else:
		raise CacheError("Encountered unknown object type while unflattening")

class VideoList:
	def __init__(self):
		self.list = []

	def addVideo(self, vf):
		self.list.append(vf)
			
	def findVideo(self, fid):
		for v in self.list:
			if v.getFileID() == fid:
				return v
			
		return None

	def __iter__(self):
		self.__index__ = 0
		return (self)

	def next(self):
		if self.__index__ < len(self.ist):
			i = self.__index__
			self.__index__ += 1
			return self.list[i]

		raise StopIteration

class VideoCache:
	def __init__(self, opts, cfg):
		self.cache = None
		self.built = None
		self.opts = opts.copy()
		self.cfg = cfg
		self.vidlist = VideoList()
		p = os.path.dirname(__file__)
		self.filename = os.path.join(p, CACHEFILE)
		
	def load(self):
		self.cache = None

		try:
			f = open(self.filename)
		except:
			print "Video Cache does not exist - attempting to build..."
			self.build()
			self.built = True
		else:
			try:
				sys.setrecursionlimit(NESTLIMIT)
				self.cache, vfl = pickle.load(f)
				unflatten(self.cache, vfl)
				self.built = False
			except CacheError:
				pass
			except:
				print "Error loading video cache - trying to build..."
				self.build()
				self.built = True
		
			f.close()

			
		return self.cache

	def loadShares(self):
		shares = []
		section = 'pytivos'
		cfg = self.cfg
		if cfg.has_section(section):
			i = 0
			while (True):
				i = i + 1
				key = "pytivo" + str(i) + ".config"
				if not cfg.has_option(section, key): break
				cfgfile = cfg.get(section, key)
				
				key = "pytivo" + str(i) + ".skip"
				skip = []
				if cfg.has_option(section, key):
					sk = cfg.get(section, key).split(",")
					skip = [s.strip() for s in sk]
					print "skipping shares (", skip, ") from pyTivo number %d" % i
				
				shares.extend(self.loadPyTivoShares(cfgfile, skip))
				
		return shares
					
	def loadPyTivoShares(self, cf, skip):
		shares = []
		pyconfig = ConfigParser.ConfigParser()
		if not pyconfig.read(cf):
			print "ERROR: pyTivo config file " + cf + " does not exist."
			return shares

		for section in pyconfig.sections():
			if not section in skip:
				if (pyconfig.has_option(section, "type") and pyconfig.get(section, "type") == "video" and 
					pyconfig.has_option(section, 'path')):
					path = pyconfig.get(section, 'path')
					shares.append([section, path, SHARETYPE_VIDEO])
					
				elif (pyconfig.has_option(section, "type") and pyconfig.get(section, "type") == "dvdvideo" and 
					pyconfig.has_option(section, 'path')):
					path = pyconfig.get(section, 'path')
					shares.append([section, path, SHARETYPE_DVD])
				
		return shares

	def build(self):
		def cmpHarvesters(a, b):
			ta = a.formatDisplayText(None)
			tb = b.formatDisplayText(None)
			return cmp(ta, tb)
		
		p = os.path.dirname(__file__)
		fn = os.path.join(p, BUILDINI)
		bcfg = ConfigParser.ConfigParser()
		
		title = "Main Menu"
		sharepage = True

		harvesters = []

		if bcfg.read(fn):
			for section in bcfg.sections():
				if section != OPTSECT:
					lopts = self.opts.copy()
					if bcfg.has_option(section, 'sort'):
						lopts['sortopt'] = bcfg.get(section,'sort').split()
					elif bcfg.has_option(section, 'sortdirection'):
						lval = bcfg.get(section, 'sortdirection').lower()
						if lval == 'down':
							lopts['sortup'] = False
						elif lval == 'up':
							lopts['sortup'] = True
						else:
							print "Error in buildcache.ini - sortdirection must be up or down"
							
					elif bcfg.has_option(section, 'display)'):
						lopts['dispopt'] = bcfg.get(section, 'display').split()
					elif bcfg.has_option(section, 'displaysep'):
						lopts['dispsep'] = bcfg.get(section, 'displaysep')

					elif bcfg.has_option(section, 'groupby'):
						lopts['group'] = bcfg.get(section, 'groupby')					
					
					if bcfg.has_option(section, 'tags'):
						h = MetaHarvester(section, lopts)
						h.setKeySet(bcfg.get(section,'tags').split())
						harvesters.append(h)
					elif bcfg.has_option(section, 'values'):
						terms = bcfg.get(section, 'values').split('/')
						vdict = {}
						for t in terms:
							v = t.split(':')
							if len(v) != 2:
								print "Error in buildcache.ini - syntax on values statement in section %s" % section
								return
							tag = v[0]
							vals = v[1].split(',')
							vdict[tag] = vals
							
						h = MetaHarvester(section, lopts)
						h.setKeyVal(vdict)
						harvesters.append(h)

			if bcfg.has_option(OPTSECT, 'sharepage'):
				v = bcfg.get(OPTSECT, 'sharepage')
				if v.lower() == 'false':
					sharepage = False

			if bcfg.has_option(OPTSECT, 'topsubtitle'):
				title = bcfg.get(OPTSECT, 'topsubtitle')


		sl = self.loadShares()
		if len(sl) == 0:
			print "Error - no shares are defined"
			self.cache = None
			return

		root = Node(title, self.opts)

		if sharepage:
			shares = Node("Browse Shares", self.opts)
			for name, path, type in sl:
				if type == SHARETYPE_VIDEO:
					print "Processing video share " + name
					s = VideoShare(self.opts, name, path, self.vidlist, harvesters)
					print "%d Videos found" % s.VideoCount()
				else: # type == SHARETYPE_DVD
					print "Processing DVD share " + name
					s = DVDShare(self.opts, name, path, self.vidlist, harvesters)
					print "%d DVD Videos found" % s.VideoCount()
					
				shares.addDir(s)
			root.addDir(shares)
		else:
			for name, path, type in sl:
				if type == SHARETYPE_VIDEO:
					print "Processing video share " + name
					s = VideoShare(self.opts, name, path, self.vidlist, harvesters)
					print "%d Videos found" % s.VideoCount()
				else: # type == SHARETYPE_DVD
					print "Processing DVD share " + name
					s = DVDShare(self.opts, name, path, self.vidlist, harvesters)
					print "%d DVD Videos found" % s.VideoCount()

				root.addDir(s)

		for h in sorted(harvesters, cmpHarvesters):
			title = h.formatDisplayText(None)
			nd = h.getNode()
			vc, gc = h.videoCount()
			if gc == None:
				print "%s count: %d videos" % (title, vc)
			else:
				print "%s count: %d videos in %d groups" % (title, vc, gc)
			root.addDir(nd)

		self.cache = root

		return root
	
	def save(self, force=False):
		if not force and self.built:
			print "Video cache not being saved because it was built dynamically on entry"
			return

		try:
			f = open(self.filename, 'w')
		except:
			print "Error opening video cache file for write"
		else:
			try:
				vfl = []
				flatten(self.cache, vfl)
				pickle.dump((self.cache, vfl), f)
			except CacheError:
				pass
			except:
				f.close()