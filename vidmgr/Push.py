from hme import *
import os
import urllib
from string import maketrans
from Config import MYKEY_PUSHRESUME, MYKEY_PUSHCOMPLETE, ConfigError
from MessageBox import MessageBox
import metadata
from time import strftime, gmtime

if os.path.sep == '/':
	quote = urllib.quote
	unquote = urllib.unquote_plus
else:
	quote = lambda x: urllib.quote(x.replace(os.path.sep, '/'))
	unquote = lambda x: os.path.normpath(urllib.unquote_plus(x))
	

class Push:
	def __init__(self, app, opts, vf):
		self.container = vf.getShare()
		self.app = app
		self.opts = opts
		self.vf = vf
		self.isactive = True
		self.submenu = None

		self.ip, self.port, self.sep = self.selectPyTivo(app, self.container)
		if self.ip == None:
			raise ConfigError("Share Configuration Error - unable to find share {%s}" % self.container)

		self.menu = []
		self.tsns = []
		for t in app.tivos:
			self.menu.append(t['name'])
			self.tsns.append(t['tsn'])

		if len(self.menu) == 0:
			raise ConfigError("Tivo Configuration Error")

		if len(self.menu) == 1:
			self.app.send_key(KEY_TIVO, MYKEY_PUSHRESUME)
			return

		self.submenu = self.app.subMenu
		self.submenu.load("Select Destination Tivo", self.menu, MYKEY_PUSHRESUME)
		return

	def handlekeypress(self, keynum, rawcode):
		if keynum == KEY_TIVO and rawcode == MYKEY_PUSHRESUME:
			tivo = 0
			if self.submenu:
				tivo = self.submenu.getResult()
				self.submenu = None

			if tivo == -1:
				self.isactive = False
				self.app.send_key(KEY_TIVO, MYKEY_PUSHCOMPLETE)
				return

			tivoname = self.menu[tivo]
			tsn = self.tsns[tivo]
		
			if self.sep is None or self.sep == os.path.sep:
				relfile = os.path.sep + self.vf.getRelativePath(self.container)
			else:
				relfile = self.sep + self.vf.getRelativePath(self.container).translate(maketrans(os.path.sep, self.sep))
			
			params = urllib.urlencode({'Command': 'Push', 'Container': self.container,
						'File': relfile,
						'tsn': tsn})
			url = 'http://%s:%s/TivoConnect' % (self.ip, self.port)

			try:
				f = urllib.urlopen(url, params)
				html = f.read()
				
			except:
				MessageBox(self.app, "Push Error",
						"An unknown exception has occurred during HTML request - verify configuration",
						'bonk',
						[[[], MYKEY_PUSHCOMPLETE]])
			else:
				if html.lower().count('queue') != 0:
					if self.opts['savepushdata']:
						self.vf.setMetaItem("pushDate", strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()))
						self.vf.setMetaItem("vPushTivo", tivoname)
						meta = self.vf.getMeta()
						try:
							fn = self.vf.getMetaFileName()
							metafile = open(fn, 'w')
							metadata.dump(metafile, meta)
							metafile.close()
						except:
							pass
					MessageBox(self.app, "Successfully Queued",
							"File has been successfully queued for push to " + tivoname,
							'alert',
							[[[], MYKEY_PUSHCOMPLETE]])
					
				else:
					MessageBox(self.app, "Push Error",
							"PyTivo responded with an unknown message (%s) push may still occur" % html,
							'alert',
							[[[], MYKEY_PUSHCOMPLETE]])

		elif self.submenu:
			self.submenu.handlekeypress(keynum, rawcode)

		else:
			self.app.sound('bonk')


	def selectPyTivo(self, app, sharename):
		for s in app.shares:
			if sharename == s['name']:
				return s['ip'], s['port'], s['sep']
			
		return None, None, None

