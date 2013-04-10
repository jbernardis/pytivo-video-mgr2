from hme import RSRC_HALIGN_LEFT, RSRC_HALIGN_RIGHT, RSRC_HALIGN_CENTER

import os
import ConfigParser
import FileID

screenHeight = 720
screenWidth = 1280

titleYPos = 36
subTitleYPos = 84

listViewSize = 14
listViewWidth = 640
listYStart = 121
listHeight = 40 
listXText = 150
listXIcon = 90 
listXCue = 30

detailViewXPos = 640
detailViewWidth = 640
detailDescHeight = 140
detailDescWidth = 590 
detailDescXPos = 10
detailDescYPos = 121

thumbnailxpos = 10
thumbnailypos = 270
thumbcachesize = 100
thumbnailheight = 450
thumbnailwidth = 620

infoHeight = 600
infoWidth = 1160

submenuheight = 166
submenuwidth = 260
submenulineheight = 30

MYKEY_PUSHRESUME = 0
MYKEY_PUSHCOMPLETE = 1
MYKEY_DELETECONFIRM = 10
MYKEY_DELETECOMPLETE = 11
MYKEY_DELETECANCEL = 12
MYKEY_REBUILDCACHE = 20

SHARETYPE_VIDEO = 0
SHARETYPE_DVD = 1

TYPE_VIDFILE = 0
TYPE_VIDDIR = 1
TYPE_DVDDIR = 2
TYPE_VIDSHARE = 3
TYPE_DVDSHARE = 4
TYPE_NODE = 5

artworkDir = "artwork"

class ConfigError(Exception):
	pass

class Config:
	def __init__(self):
		fn = os.path.join(os.path.dirname(__file__), "vidmgr.ini")

		self.cfg = ConfigParser.ConfigParser()
		if not self.cfg.read(fn):
			raise ConfigError("ERROR: vidmgr configuration file does not exist.")

	def getConfigParser(self):
		return self.cfg
	
	def load(self):
		opts = {
				'goodexts' : ['.mp4', '.mpg', '.avi', '.wmv'],
				'metaignore' : ['isEpisode', 'isEpisodic', '__fileName', '__filePath'],
				'metafirst' : ['title', 'seriesTitle', 'episodeTitle', 'description' ],
				'metaspacebefore' : [],
				'metaspaceafter' : [],
				'metamergefiles' : True,
				'metamergelines' : False,
				'infolabelpercent' : 30,
				'inforightmargin' : 20,
				'descsize' : 20,
				'skin' : None,
				'deleteallowed' : True,
				'thumbjustify' : RSRC_HALIGN_LEFT,
				'thumbfolderfn' : 'folder.jpg',
				'dispopt' : ['title', 'episodeTitle'],
				'dispsep' : ":",
				'sortopt' : ['title', 'episodeTitle'],
				'sortup' : True,
				'tagssortup' : True,
				'ignorearticle' : True,
				'group' : None,
				'usefileid' : True,
				'savepushdate' : False
				}
	
		if self.cfg.has_section('vidmgr'):
			for opt, value in self.cfg.items('vidmgr'):
				lval = value.lower()
				# options for metadata on the info screen
				if opt == 'exts':
					opts['goodexts'] = value.split()
	
				elif opt == 'metaignore':
					opts['metaignore'] = value.split()
	
				elif opt == 'metafirst':
					opts['metafirst'] = value.split()
	
				elif opt == 'metaspacebefore':
					opts['metaspacebefore'] = value.split()
				
				elif opt == 'metaspace' or opt == 'metaspaceafter':
					opts['metaspaceafter'] = value.split()
	
				elif opt == 'metamergefiles':
					if lval == "false":
						opts['metamergefiles'] = False
				
				elif opt == 'metamergelines':
					if lval == "true":
						opts['metamergelines'] = True
				
				elif opt == 'savepushdate':
					if lval == "true":
						opts['savepushdate'] = True
				
				elif opt == 'infolabelpercent':
					n = int(value)
					if n < 0 or n > 70:
						raise ConfigError("Config error - infolabelpercent value out of bounds (0-70)")
					else:
						opts['infolabelpercent'] = n
	
				elif opt == 'inforightmargin':
					n = int(value)
					if n < 0 or n > 100:
						raise ConfigError("Config error - inforightmargin value out of bounds (0-100)")
					else:
						opts['inforightmargin'] = n
				
				elif opt == 'descsize':
					opts['descsize'] = int(value)
	
				elif opt == 'skin':
					opts['skin'] = value
	
				elif opt == 'deleteallowed':
					if lval == "false":
						opts['deleteallowed'] = False
	
				elif opt == 'thumbjustify':
					if lval == 'center':
						opts['thumbjustify'] = RSRC_HALIGN_CENTER
					elif lval == 'right':
						opts['thumbjustify'] = RSRC_HALIGN_RIGHT
					elif lval == 'left':
						opts['thumbjustify'] = RSRC_HALIGN_LEFT
					else:
						raise ConfigError("Config error - invalid value for thumbjustify (left, center, right)")
	
				elif opt == 'thumbfolderfn':
					opts['thumbfolderfn'] = value

				elif opt == 'display':
					opts['dispopt'] = value.split()
	
				elif opt == 'displaysep':
					opts['dispsep'] = value
	
				elif opt == 'sort':
					opts['sortopt'] = value.split()
					
				elif opt == 'sortdirection':
					if lval == 'down':
						opts['sortup'] = False
					elif lval == 'up':
						opts['sortup'] = True
					else:
						raise ConfigError("Config error - sortdirection must be up or down")
	
				elif opt == 'ignorearticle':
					if lval == "false":
						opts['ignorearticle'] = False
						
				elif opt == 'usefileid':
					if lval == "false":
						opts['usefileid'] = False
				
				elif opt in ['sharepage', 'topsubtitle', 'sortroot']:
					pass # these are handled by cache building logic
				
				else:
					raise ConfigError("Config error - unknown option (%s)" % opt)
	
		FileID.setFileIDOption(opts['usefileid'])
		return opts

def addLocalOpts(opts, root, path):
	cfgfn = os.path.join(root, path, ".vidmgr.ini")
	cfg = ConfigParser.ConfigParser()
	if not cfg.read(cfgfn):
		return
	
	if cfg.has_section('vidmgr'):
		for opt, value in cfg.items('vidmgr'):
			lval = value.lower()
			if opt == 'deleteallowed':
				if lval == "false":
					opts['deleteallowed'] = False
				elif lval == "true":
					opts['deleteallowed'] = True
				else:
					print "Invalid value for deleteallowed in %s" % cfgfn

			elif opt == 'display':
				opts['dispopt'] = value.split()

			elif opt == 'displaysep':
				opts['dispsep'] = value

			elif opt == 'sortdirection':
				if lval == 'down':
					opts['sortup'] = False
				elif lval == 'up':
					opts['sortup'] = True
				else:
					print "Invalid value for sortdirection (up, down) in %s" % cfgfn

			elif opt == 'sort':
				opts['sortopt'] = value.split()

			else:
				print "Invalid option (%s) in %s" % (opt, cfgfn)

