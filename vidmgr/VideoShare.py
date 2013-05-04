'''
Created on Aug 3, 2011

@author: Jeff
'''
from VideoFile import VideoFile
from VideoDir import VideoDir
from Config import TYPE_VIDSHARE
import Config
import os.path
import metadata
from FileID import fileId

def myWalk(directory):
	dirlist = []
	filelist = []
	
	if os.path.islink(directory):
		ldir = os.path.realpath(directory)
		print "Processing symlink: %s => %s" % (directory, ldir)
	else:
		ldir = directory

	l = os.listdir(ldir)
	for d in l:
		fd = os.path.join(ldir, d)
		if os.path.isdir(fd):
			dirlist.append(d)
		else:
			filelist.append(d)

	result = [[directory, dirlist, filelist],]
	for d in dirlist:
		result.extend(myWalk(os.path.join(directory, d)))

	return result


class VideoShare:
	def __init__(self, opts, name, root, vidlist, harvesters):
		self.name = name
		self.title = name
		self.opts = opts.copy()
		self.count = 0
		self.root = root
		self.videoDir = VideoDir(opts, "", "", root, name)
		
		tree = myWalk(root)
		
		sharedirs = {"": self.videoDir}
		shareopts = {"": self.opts}

		for path, dirs, files in tree:
			rpath = path[len(root):]
			if rpath.startswith(os.path.sep): rpath = rpath[1:]
			if rpath not in sharedirs: continue
			vl = sharedirs[rpath]
			lopts = shareopts[rpath]
			Config.addLocalOpts(lopts, root, rpath)
			vl.setOpts(lopts)
			
			for name in dirs:
				if name.startswith("."): continue
				meta = metadata.from_text(os.path.join(path, name, "folder"),
							lopts['metamergefiles'],
							lopts['metamergelines'])
				d = VideoDir(lopts, name, rpath, path, self.name)
				d.setMeta(meta)
				vl.addDir(d)
				sharedirs[os.path.join(rpath, name)] = d
				shareopts[os.path.join(rpath, name)] = lopts.copy()
			
			for name in files:
				if name.startswith("."): continue
				if os.path.splitext(name)[1].lower() in lopts['goodexts']:
					fid = fileId(os.path.join(path, name))
					if fid != None:		
						vf = vidlist.findVideo(fid)
					else:
						vf = None
						
					if vf == None:
						vf = VideoFile(lopts, path, name, fid)
						vidlist.addVideo(vf)

						meta = metadata.from_text(os.path.join(path, name),
												lopts['metamergefiles'],
												lopts['metamergelines'])
						if not 'title' in meta:
							meta = metadata.basic(os.path.join(path, name))
						vf.setMeta(meta)

						vl.addVideo(vf)
						self.count += 1
						
						for h in harvesters:
							h.harvest(vf)

					else:
						vl.addVideo(vf, path=path, fn=name)
						self.count += 1
						
			vl.sort()
			
	def getObjType(self):
		return TYPE_VIDSHARE
						
	def __iter__(self):
		return self.videoDir.__iter__()
	
	def __len__(self):
		return self.videoDir.__len__()
	
	def getMeta(self):
		return self.videoDir.getMeta()
	
	def getItem(self, x):
		return self.videoDir.getItem(x)
	
	def formatDisplayText(self, fmt):
		return self.title
	
	def formatSortText(self, fmt):
		return self.title
	
	def getOpts(self):
		return self.opts
	
	def getFullTitle(self):
		return self.title
					
	def getVideoDir(self):
		return self.videoDir
	
	def getRoot(self):
		return self.root
	
	def VideoCount(self):
		return self.count

	def __str__(self):
		s = "Name: " + self.name + "\n" + "Root: " + self.root + "\n" + str(self.videoDir)
		return s
