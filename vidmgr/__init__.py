from hme import *
import os
import socket
import metadata
import cPickle as pickle
import ConfigParser
import urllib
from time import asctime
from string import maketrans
from ThumbCache import ThumbCache
import Config
from Config import ( screenWidth, screenHeight, titleYPos, subTitleYPos, 
		MYKEY_PUSHCOMPLETE, MYKEY_DELETECONFIRM, MYKEY_DELETECOMPLETE, MYKEY_DELETECANCEL, MYKEY_REBUILDCACHE,
		infoWidth, infoHeight, thumbnailheight, thumbnailwidth, thumbcachesize, ConfigError, TYPE_VIDFILE )

from ListDisplayManager import ListDisplayManager
from DetailDisplayManager import DetailDisplayManager
from VideoCache import VideoCache
from VideoFile import VideoFile
from VideoDir import VideoDir
from InfoView import InfoView
from SubMenu import SubMenu
from Push import Push
from MessageBox import MessageBox

TITLE = 'PyTivo Video Manager'
VERSION = '2.2b'

print asctime(), TITLE + " version " + VERSION + " module initializing"

AppPath = os.path.dirname(__file__)

tc = ThumbCache(AppPath, thumbcachesize, thumbnailwidth, thumbnailheight)

class Images:
	def __init__(self, app):
		self.Background    = self.loadimage(app, 'background')
		self.CueUp         = self.loadimage(app, 'cueup')
		self.CueDown       = self.loadimage(app, 'cuedown')
		self.CueLeft       = self.loadimage(app, 'cueleft')
		self.HiLite        = self.loadimage(app, 'hilite')
		self.SubMenu       = self.loadimage(app, 'submenu')
		self.MenuHiLite    = self.loadimage(app, 'menuhilite')
		self.IconFolder    = self.loadimage(app, 'folder')
		self.IconVideo     = self.loadimage(app, 'video')
		self.IconDVDFolder = self.loadimage(app, 'dvdfolder')
		self.IconDVDVideo  = self.loadimage(app, 'dvdvideo')
		self.Info          = self.loadimage(app, 'info')
		self.InfoUp        = self.loadimage(app, 'infoup')
		self.InfoDown      = self.loadimage(app, 'infodown')
		self.MsgBox        = self.loadimage(app, 'msgbox')
	
	def loadimage(self, app, name):
		skin = app.opts['skin']
		if skin != None:
			fn = os.path.join(AppPath, 'skins', skin, name + ".png")
			if os.path.exists(fn):
				return Image(app, fn)
			
		fn = os.path.join(AppPath, 'skins', name + ".png")
		if os.path.exists(fn):
			return Image(app, fn)
		
		if skin == None:
			print "image '" + name + "' missing for default skin"
		else:
			print "image '" + name + "' missing for skin '" + skin + "'"
		return None
			

class Fonts:
	def __init__(self, app):
		self.fnt16 = Font(app, size=16)
		self.fnt20 = Font(app, size=20)
		self.fnt24 = Font(app, size=24)
		self.fnt30 = Font(app, size=30)
		self.descfont = Font(app, size=app.opts['descsize'])
		self.infofont = Font(app, size=24, flags=FONT_METRICS_BASIC|FONT_METRICS_GLYPH)
	
class Vidmgr(Application):
	def handle_resolution(self):
		print "Vidmgr Entering Handle Resolution"
		for (hres, vres, x, y) in self.resolutions:
			print "   Checking resolution %d, %d" %(hres, vres)
			if (hres == 1280):
				print "  Found an HD resolution"
				return (hres, vres, x, y)
			
		print "NO HD resolutions found!!!"
		self.active = False
		self.sound('bonk')
		return self.resolutions[0]
	
	def startup(self):
		print "Vidmgr thread entering startup"
		self.vwInfo = None
		self.vcChanged = False
		config = Config.Config()
		self.opts = config.load()
		self.cp = config.getConfigParser()
					
		# get the tivo information out of the startup config file.  For each tivo, we need to know:
		# tivox.name - the user friendly name and
		# tivox.tsn - the TSN
		# these fields all go into a section named [tivos]		
		self.loadTivos(self.cp, self.opts['sorttivosbyname'])
		if len(self.tivos) == 0:
			raise ConfigError("No Tivos found - exiting")

		# get the pytivo information.  For each pytivo instance, we need the following:
		# pytivox.config - the location of the config file
		# pytivox.ip - the ip address
		#
		# also, if the pytivo port number is not specified in the pytivo config file, you must have
		# pytivox.port - the port number
		self.shares = []		
		self.loadShares(self.cp)
		if len(self.shares) == 0:
			raise ConfigError("No shares found - exiting")
		
	def cleanup(self):
		tc.save()
		if self.vcChanged:
			self.vc.save()
		
	def handle_active(self):
		print "Vidmgr thread activating"
		self.myimages = Images(self)
		self.myfonts = Fonts(self)
		self.tdcount = 0

		self.push = None
		self.msgbox = None
		self.rebuildingCache = False
		
		self.vc = VideoCache(self.opts, self.cp)
		
		self.root.set_resource(self.myimages.Background)
		self.TitleView = View(self, height=30, width=screenWidth, ypos=titleYPos)
		self.SubTitleView= View(self, height=20, width=screenWidth, ypos=subTitleYPos)
		
		self.ldm = ListDisplayManager(self, self.opts)
		self.ddm = DetailDisplayManager(self, self.opts, tc)
		self.vwInfo = InfoView(self, self.opts, self.myfonts.infofont)
		self.subMenu = SubMenu(self, self.opts)

		self.rootNode = self.vc.load()
		self.vcChanged = False

		self.start()

	def reStart(self):
		self.ldm.ReInit()
		self.start()
		
	def start(self):
		if self.rootNode == None:
			raise ConfigError("No video cache - exiting")

		self.TitleView.set_text(TITLE, font=self.myfonts.fnt30, colornum=0xffffff, flags=RSRC_VALIGN_BOTTOM)
		self.SubTitleView.set_text(self.rootNode.getFullTitle(), font=self.app.myfonts.fnt20, colornum=0xffffff, flags=RSRC_VALIGN_BOTTOM)

		self.currentNode, self.currentItem = self.ldm.Descend(self.rootNode)
		self.lopts = self.rootNode.getOpts()
		self.ddm.show(self.currentItem)
		
		if self.currentNode == None:
			print "Current node = NULL - exiting"
			self.active = False
			
	def handle_font_info(self, font):
		if self.vwInfo == None:
			print "Got handle font before vwInfo was instantiated ??"
		else:
			self.vwInfo.setinfogeometry(font)
			
	def handle_key_press(self, keynum, rawcode):
		if keynum == KEY_THUMBSDOWN:
			self.tdcount += 1
			if self.tdcount == 3:
				self.mb = MessageBox(self.app, "Rebuilding Cache...",
					"Please Wait",
					'alert',
					[[[KEY_TIVO], 0]])

				self.send_key(KEY_TIVO, MYKEY_REBUILDCACHE)
				self.rebuildingCache = True
				return

			self.sound('thumbsup')
			return
		else:
			self.tdcount = 0
			
		if keynum == KEY_TIVO and rawcode == MYKEY_REBUILDCACHE:
			self.rootNode = self.vc.build()
			self.vcChanged = True

			self.mb.close()
			self.reStart()
			return

		if self.msgbox:
			self.msgbox.handlekeypress(keynum, rawcode)
			
		elif self.vwInfo.isVisible:
			snd = 'updown'
			if keynum in [ KEY_LEFT, KEY_CLEAR, KEY_INFO ]:
				self.vwInfo.hide()
				
			elif keynum in [ KEY_DOWN, KEY_CHANNELDOWN ]:
				if not self.vwInfo.pagedown():
					snd = 'bonk'
					
			elif keynum in [ KEY_UP, KEY_CHANNELUP ]:
				if not self.vwInfo.pageup():
					snd = 'bonk'
					
			else:
				snd = 'bonk'
				
			self.sound(snd)

		elif self.push:
			if keynum == KEY_TIVO and rawcode == MYKEY_PUSHCOMPLETE:
				self.push = None
			else:
				self.push.handlekeypress(keynum, rawcode)
				
		elif self.currentItem == None and keynum not in [ KEY_LEFT, KEY_TIVO ]:
			self.sound('bonk')
				
		elif keynum == KEY_INFO:
			meta = self.currentItem.getMeta()
			if len(meta) == 0:
				snd = 'bonk'
			else:
				self.vwInfo.loadmetadata(meta)
				self.vwInfo.paint()
				self.vwInfo.show()
				snd = 'updown'
			self.sound(snd)
				
		elif self.ldm.isNavKey(keynum, rawcode):
			self.currentItem = self.ldm.Navigate(keynum, rawcode)
			self.ddm.show(self.currentItem)
			
		elif keynum == KEY_LEFT:
			self.currentNode, self.currentItem = self.ldm.Ascend()
			if self.currentNode == None:
				self.active = False
				return
			self.SubTitleView.set_text(self.currentNode.getFullTitle(),
						font=self.app.myfonts.fnt20,
						colornum=0xffffff, flags=RSRC_VALIGN_BOTTOM)
			self.ddm.show(self.currentItem)
			self.sound('updown')
			
		elif keynum in [KEY_RIGHT, KEY_SELECT]:
			if self.currentItem.getObjType() == TYPE_VIDFILE:
				self.push = Push(self, self.opts, self.currentItem)
			else:
				self.SubTitleView.set_text(self.currentItem.getFullTitle(),
								font=self.app.myfonts.fnt20,
								colornum=0xffffff, flags=RSRC_VALIGN_BOTTOM)
				self.lopts = self.currentItem.getOpts()
				self.currentNode, self.currentItem = self.ldm.Descend(self.currentItem)
			self.ddm.show(self.currentItem)
			self.sound('updown')
			
		elif keynum == KEY_CLEAR:
			if not self.deletable(self.currentItem):
				self.sound('bonk')
			else:
				MessageBox(self.app, "Delete Confirmation",
						"Press THUMBS-UP button to confirm deletion of " + 
						self.currentItem.formatDisplayText(self.lopts['dispopt']),
						'alert',
						[
						 [[KEY_THUMBSUP], MYKEY_DELETECONFIRM], 
						 [[], MYKEY_DELETECANCEL]
						])
				
		elif keynum == KEY_TIVO and rawcode == MYKEY_DELETECOMPLETE:
			pass # nothing to do here
		
		elif keynum == KEY_TIVO and rawcode == MYKEY_DELETECANCEL:
			m = MessageBox(self.app, "Delete Cancelled",
					"CANCELLED",
					'bonk',
					[[[KEY_TIVO], 0]])
			self.sleep(1)
			m.close()
		
		elif keynum == KEY_TIVO and rawcode == MYKEY_DELETECONFIRM:
			m = MessageBox(self.app, "Deleting...",
					"Please Wait",
					'updown',
					[[[KEY_TIVO], 0]])
			self.currentItem.delVideo()
			self.currentItem = self.ldm.Verify()
			self.ddm.show(self.currentItem)
			m.close()
			MessageBox(self.app, "Deleted",
					"Video/Metadata/Artwork Deleted - Press any key",
					'alert',
					[[[], MYKEY_DELETECOMPLETE]])
			self.vcChanged = True
		
		else:
			self.sound('bonk')

	def deletable(self, item):
		if item.getObjType() != TYPE_VIDFILE:
			return False
		
		if item.isDeletable():
			return True
		
		return False
		
	# load up tivo information from the config file
	def loadTivos(self, cfg, sortflag):
		def cmptivo (left, right):
			return cmp(left['name'], right['name'])
		
		tlist = []
		section = 'tivos'
		
		allchars = maketrans('', '')
		if cfg.has_section(section):
			i = 0
			while (True):
				i = i + 1
				namekey = 'tivo' + str(i) + '.name'
				tsnkey = 'tivo' + str(i) +  '.tsn'
				if cfg.has_option(section, namekey) and cfg.has_option(section, tsnkey):
					tlist.append({'name' : cfg.get(section, namekey),
									'tsn' : cfg.get(section, tsnkey).translate(allchars, '-')})
				else:
					break
				
		if sortflag:
			self.tivos = sorted(tlist, cmp=cmptivo)
		else:
			self.tivos = tlist[:]

	# load up pytivo and shares information from config and from pytivo config(s)
	def loadShares(self, cfg):
		self.shares = []
		
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(('4.2.2.1', 123))
		defip = s.getsockname()[0]
	
		section = 'pytivos'
		if cfg.has_section(section):
			i = 0
			while (True):
				i = i + 1
				key = "pytivo" + str(i) + ".config"
				if not cfg.has_option(section, key): break
				cfgfile = cfg.get(section, key)
				
				sep = None
				sepkey = 'pytivo' + str(i) + '.sep'
				if cfg.has_option(section, sepkey): sep = cfg.get(section, sepkey)
				
				ip = defip
				key = "pytivo" + str(i) + ".ip"
				if cfg.has_option(section, key):
					ip = cfg.get(section, key)

				port = None				
				key = "pytivo" + str(i) + ".port"
				if cfg.has_option(section, key):
					port = cfg.get(section, key)
					
				key = "pytivo" + str(i) + ".skip"
				skip = []
				if cfg.has_option(section, key):
					sk = cfg.get(section, key).split(",")
					skip = [s.strip() for s in sk]
				
				self.loadPyTivoConfig(cfgfile, ip, port, sep, skip)
					

	# parse a pytivo config looking for shares				
	def loadPyTivoConfig(self, cf, ip, defport, sep, skip):
		pyconfig = ConfigParser.ConfigParser()
		if not pyconfig.read(cf):
			raise ConfigError("ERROR: pyTivo config file " + cf + " does not exist.")

		port = defport
		if pyconfig.has_option('Server', 'port') : port = pyconfig.get('Server', 'port')
		
		if port == None:
			raise ConfigError("Neither main config file nor pytivo config file " + cf + " has port number specified")
		
		for section in pyconfig.sections():
			if not section in skip:
				if (pyconfig.has_option(section, "type")
						and (pyconfig.get(section, "type") == "video" or pyconfig.get(section, "type") == "dvdvideo")
						and	pyconfig.has_option(section, 'path')):
					path = pyconfig.get(section, 'path')
					self.shares.append({'name' : section,
							'ip' : ip,
							'port' : port,
							'path' : path,
							'sep' : sep})

		
