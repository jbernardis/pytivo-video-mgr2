from VideoFile import VideoFile
from VideoDir import VideoDir
from DVDDir import DVDDir
from FileID import fileId
from Config import TYPE_DVDSHARE
import Config
import os
import metadata
import re

regex = re.compile(r'^Title\s*(\d+)$')

class DVDShare:
	def __init__(self, opts, name, root, vidlist, harvesters):
		self.name = name
		self.title = name
		self.opts = opts.copy()
		self.count = 0
		self.root = root

		self.videoDir = VideoDir(self.opts, "", "", root, name)
		
		shareopts = {"": self.opts}
		sharedirs = {"": self.videoDir}

		tree = os.walk(root)

		for path, dirs, files in tree:
			rpath = path[len(root):]
			if rpath.startswith(os.path.sep): rpath = rpath[1:]

			if rpath not in sharedirs: continue
			vdir = sharedirs[rpath]
			lopts = shareopts[rpath]
			Config.addLocalOpts(lopts, root, rpath)
			vdir.setOpts(lopts)

			if self.isDvdDir(path):
				p, deftitle = os.path.split(path)
				meta, titles = self.loadDvdMeta(path, lopts, "default", deftitle, False)
				fid = fileId(os.path.join(path, "default.txt"))
				for (title, fn, tn) in titles:
					if fid != None:		
						vf = vidlist.findVideo((fid, tn))
					else:
						vf = None
						
					if vf == None:
						vf = VideoFile(lopts, path, fn, (fid, tn))
						vidlist.addVideo(vf)

						meta, t = self.loadDvdMeta(path, lopts, fn, title, True)
						meta['title'] = title
						meta['titleNumber'] = tn
						vf.setMeta(meta)
						
						vdir.addVideo(vf)
						self.count += 1

						for h in harvesters:
							h.harvest(vf)

					else:
						vdir.addVideo(vf, path=path, fn=fn)
						self.count += 1
			else:
				for dn in dirs:
					if dn.startswith("."): continue

					cdir = os.path.join(path, dn)
					if self.isDvdDir(cdir):
						meta, tnames = self.loadDvdMeta(cdir,
							lopts,
							"default",
							dn,
							False)
					
						d = DVDDir(lopts, dn, rpath, path, self.name)
					else:
						meta = metadata.from_text(
							os.path.join(path, dn, "folder"),
							lopts['metamergefiles'],
							lopts['metamergelines'], lopts['metamergeparent'])

						d = VideoDir(lopts, dn, rpath, path, self.name)
						
					d.setMeta(meta)
					vdir.addDir(d)
					sharedirs[os.path.join(rpath, dn)] = d
					shareopts[os.path.join(rpath, dn)] = lopts.copy()
			vdir.sort()
		
	def getObjType(self):
		return TYPE_DVDSHARE


	def isDvdDir(self, dir):
		dvddir = os.path.join(dir, "VIDEO_TS")
		return os.path.isdir(dvddir)

	def loadDvdMeta(self, metadir, opts, basefn, deftitle, singleDVDtitle):
		metapath = os.path.join(metadir, basefn)
		meta = metadata.from_text(metapath, opts['metamergefiles'], opts['metamergelines'], lopts['metamergeparent'])
		if (not 'title' in meta) or (meta['title'] == basefn):
			meta['title'] = deftitle

		titles = []
		kl = meta.keys()
		for k in kl:
			x = regex.search(k)
			if x:
				tn = int(x.group(1))
				if meta[k].lower().startswith("ignore"):
					del(meta[k])
				else:
					filename = "__T%02d.mpg" % tn
					titles.append((meta[k], filename, tn))

					if (singleDVDtitle):
						del(meta[k])

		if len(titles) == 0:
			titles.append((meta['title'], "__T00.mpg", 0))
			
		return (meta, titles)

	def __iter__(self):
		return self.videoDir.__iter__()
	
	def __len__(self):
		return self.videoDir.__len__()
	
	def getMeta(self):
		return self.videoDir.getMeta()
	
	def getOpts(self):
		return self.opts
	
	def getItem(self, x):
		return self.videoDir.getItem(x)
	
	def formatDisplayText(self, fmt):
		return self.title
	
	def formatSortText(self, fmt):
		return self.title
	
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
