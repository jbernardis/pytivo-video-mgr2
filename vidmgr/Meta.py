'''
Created on Aug 4, 2011

@author: Jeff
'''

from Node import Node, OTHER
from Config import ConfigError
from InfoView import metaTranslate
from VideoFile import stripArticle

import os
import unicodedata
import string

AlphaKeys = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

validFilenameChars = "-_%s%s" % (string.ascii_letters, string.digits)
transtable = string.maketrans(" ", "-")

def Legalize(s):
	cs = unicodedata.normalize('NFKD', unicode(s)).encode('ASCII', 'ignore').translate(transtable)
	return ''.join(c for c in cs if c in validFilenameChars)

class Harvester:
	def __init__(self, name, opts):
		self.name = name
		self.hpath = Legalize(name)
		self.opts = opts.copy()
		groupTag = self.opts['group']
		if groupTag == None:
			self.root = Node(name, opts, path=self.hpath)
		else:
			self.root = Node(name, opts, path=self.hpath, title = "%s (grouped by %s)" % (name, metaTranslate(groupTag)))
			
		self.nodeMap = {}
		self.pathMap = {}
		self.pathMap[name] = self.hpath
		self.count = 0
		self.gcount = 0
		
	def getPathMap(self):
		return self.pathMap
		
	def formatDisplayText(self, fmt):
		n = self.name
		groupTag = self.opts['group']
		if groupTag:
			n += " (grouped by %s)" % metaTranslate(groupTag)

		return n
	
	def getNode(self):
		self.root.sort()
		for n in self.nodeMap.keys():
			self.nodeMap[n].sort()
			
		return self.root
	
	def videoCount(self):
		if self.opts['group'] == None:
			return (self.count, None)
		else:
			return (self.count, self.gcount)
		
	def harvest(self, vf):
		if self.opts['shares']:
			# skip the video unless it's in one of the shares
			# we are including
			found = False
			vfsl = vf.getShareList();
			for s in self.opts['shares']:
				if s in vfsl:
					found = True
					break
			if not found:
				return False
		
		return True

class AllHarvester(Harvester):	
	def __init__(self, name, opts, verbose=False):
		Harvester.__init__(self, name, opts)
		self.verbose=verbose
		
	def harvest(self, vf):	
		if not Harvester.harvest(self, vf):
			return
		
		mvf = vf.getMeta()
		# determine grouping
		groupTag = self.opts['group']
		if groupTag == None:
			# no grouping - stuff into root node
			target = self.root
		else:
			# get the grouping value
			if groupTag not in mvf:
				grp = OTHER
			else:
				grp = mvf[groupTag]
				if type(grp) is list:
					raise ConfigError("Configuration Error - grouping item must not be a list")

			if grp in self.nodeMap:
				# if we've seen this group, then just reuse the 
				# same node
				target = self.nodeMap[grp]
			else:
				# Otherwise create a new node and link it in
				path=os.path.join(self.hpath, Legalize(grp))
				target = Node(grp, self.opts, path=path, title = "%s: %s" %(metaTranslate(groupTag), grp))
				self.pathMap[os.path.join(self.name, grp)] = path
				self.nodeMap[grp] = target
				self.root.addDir(target)
				self.gcount += 1
		
		target.addVideo(vf)
		self.count += 1

class AlphaHarvester(Harvester):
	def __init__(self, name, opts, metakey, verbose=False):
		Harvester.__init__(self, name, opts)
		self.metakey = metakey
		self.verbose = verbose

	def harvest(self, vf):	
		if not Harvester.harvest(self, vf):
			return
		# get the metadata for the video we are trying to add
		mvf = vf.getMeta()
		k = self.metakey
		if not k in mvf:
			return
		
		if type(mvf[k]) is list:
			raise ConfigError("Configuration Error - tag for alpha cannot be a list")
		
		if k in [ 'title', 'episodeTitle' ] and self.opts['ignorearticle']:
			data = stripArticle(mvf[k])
		else:
			data = mvf[k]
			
		keychar = data[0].upper()
		if keychar not in AlphaKeys:
			keychar = OTHER
			
		groupTag = self.opts['group']
		if groupTag == None:
			# no grouping for this share OR video does not have
			# grouping metadata item
			if keychar not in self.nodeMap:
				# we've not seen this value yet - create a Node
				# and link it in
				path=os.path.join(self.hpath, Legalize(keychar))
				target = Node(keychar + "... ", self.opts, path=path)
				self.pathMap[os.path.join(self.name, keychar)] = path
				self.nodeMap[keychar] = target
				self.root.addDir(target)
			else:
				# otherwise we've seen it so just use it
				target = self.nodeMap[keychar]
					
		else:
			# otherwise we are grouping
			if groupTag not in mvf:
				grp = OTHER
			else:
				grp = mvf[groupTag]
				if type(grp) is list:
					raise ConfigError ("Configuration Error - grouping item must not be a list")
	
			grpTitle = "%s: %s" % (metaTranslate(groupTag), grp)
			if grp not in self.nodeMap:
				path=os.path.join(self.hpath, Legalize(grp))
				grpNode = Node(grp, self.opts, title = grpTitle, path=path)
				self.pathMap[os.path.join(self.name, grp)] = path
				self.nodeMap[grp] = grpNode
				self.root.addDir(grpNode)
				self.gcount += 1
			else:
				grpNode = self.nodeMap[grp]
					
			mvkey = grpTitle + "/" + keychar
			if mvkey not in self.nodeMap:
				path=os.path.join(self.hpath, Legalize(grp), Legalize(keychar))
				target = Node(keychar + "... ", self.opts, title = mvkey + "...", path=path)
				self.pathMap[os.path.join(self.name, grp, keychar)] = path
				self.nodeMap[mvkey] = target
				grpNode.addDir(target)
			else:
				target = self.nodeMap[mvkey]
				
		target.addVideo(vf)
		self.count += 1
		
class KeyValHarvester(Harvester):
	def __init__(self, name, opts, metakeydict, verbose=False):
		Harvester.__init__(self, name, opts)
		self.metakeydict = metakeydict.copy()
		self.verbose = verbose
			
	def harvest(self, vf):
		if not Harvester.harvest(self, vf):
			return
		# get the metadata for the video we are trying to add
		mvf = vf.getMeta()
		
			# now go through our dictionary of matching tags
		for k in self.metakeydict.keys():
			# if a tag is NOT in the video, then do not
			# include that video here
			if not k in mvf:
				return

			# otherwise - get the list og values for that
			# metadata item from our map			
			l = self.metakeydict[k]
			if type(mvf[k]) is list:
				# if the metadata item is a list, then
				# success == the intersection between
				# the two lists is not empty
				match = 0
				for mv in mvf[k]:
					if mv in l:
						match += 1

				if match == 0:
					# no matches here - video does not qualify
					return
			else:
				# otherwise it's not a list - so make
				# sure our matching value is in the
				# metadata
				if not mvf[k] in l:
					return
				
		# we passed all checks - so add this video
		
		# determine grouping
		groupTag = self.opts['group']
		if groupTag == None:
			# no grouping - stuff into root node
			target = self.root
		else:
			# get the grouping value
			if groupTag not in mvf:
				grp = OTHER
			else:
				grp = mvf[groupTag]
				if type(grp) is list:
					raise ConfigError("Configuration Error - grouping item must not be a list")

			if grp in self.nodeMap:
				# if we've seen this group, then just reuse the 
				# same node
				target = self.nodeMap[grp]
			else:
				# Otherwise create a new node and link it in
				path=os.path.join(self.hpath, Legalize(grp))
				target = Node(grp, self.opts, title = "%s: %s" %(metaTranslate(groupTag), grp), path=path)
				self.pathMap[os.path.join(self.name, grp)] = path
				self.nodeMap[grp] = target
				self.root.addDir(target)
				self.gcount += 1
		
		target.addVideo(vf)
		self.count += 1
		
class KeySetHarvester(Harvester):
	def __init__(self, name, opts, metakeys, verbose=False):
		Harvester.__init__(self, name, opts)
		self.metakeys = [k for k in metakeys]
		self.verbose = verbose

	def harvest(self, vf):
		if not Harvester.harvest(self, vf):
			return
		# get the metadata for the video
		mvf = vf.getMeta()
		groupTag = self.opts['group']
		
		addlist = []
		
		# now scan through our list of keys
		mkmatch = 0
		for mk in self.metakeys:	
			# check if the video even has this key	
			if mk in mvf:
				mkmatch += 1
				# it does - get the values and build up our worklist
				if type(mvf[mk]) is list:
					for mv in mvf[mk]:
						if mv not in addlist:
							addlist.append(mv)
				else:
					mv = mvf[mk]
					if mv not in addlist:
						addlist.append(mv)
						
		if mkmatch == 0 and self.verbose:
			print "%s does not have any of meta tag(s) %s" % (vf.getFullPath(), str(self.metakeys))
					
		# now go through the worklist and build the structure as we go
		tally = False
		for mv in addlist:
			if groupTag == None:
				# no grouping for this share OR video does not have
				# grouping metadata item
				if mv not in self.nodeMap:
					# we've not seen this value yet - create a Node
					# and link it in
					path=os.path.join(self.hpath, Legalize(mv))
					target = Node(mv, self.opts, path=path)
					self.pathMap[os.path.join(self.name, mv)] = path
					self.nodeMap[mv] = target
					self.root.addDir(target)
				else:
					# otherwise we've seen it so just use it
					target = self.nodeMap[mv]
					
			else:
				# otherwise we are grouping
				if groupTag not in mvf:
					grp = OTHER
				else:
					grp = mvf[groupTag]
					if type(grp) is list:
						raise ConfigError ("Configuration Error - grouping item must not be a list")

				grpTitle = "%s: %s" % (metaTranslate(groupTag), grp)
				if grp not in self.nodeMap:
					path=os.path.join(self.hpath, Legalize(grp))
					grpNode = Node(grp, self.opts, title = grpTitle, path=path)
					self.pathMap[os.path.join(self.name, grp)] = path
					self.nodeMap[grp] = grpNode
					self.root.addDir(grpNode)
					self.gcount += 1
				else:
					grpNode = self.nodeMap[grp]
					
				mvkey = grpTitle + "/" + mv
				if mvkey not in self.nodeMap:
					path=os.path.join(self.hpath, Legalize(grp), Legalize(mv))
					target = Node(mv, self.opts, title = mvkey, path=path)
					self.pathMap[os.path.join(self.name, grp, mv)] = path
					self.nodeMap[mvkey] = target
					grpNode.addDir(target)
				else:
					target = self.nodeMap[mvkey]
					
			target.addVideo(vf)
			tally = True
			
		if tally:
			self.count += 1

