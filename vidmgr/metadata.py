#!/usr/bin/env python

import os
from datetime import datetime
from xml.dom import minidom
from xml.parsers import expat

# Something to strip
TV_RATINGS = {'TV-Y7': 'x1', 'TV-Y': 'x2', 'TV-G': 'x3', 'TV-PG': 'x4', 
			  'TV-14': 'x5', 'TV-MA': 'x6', 'TV-NR': 'x7',
			  'TVY7': 'x1', 'TVY': 'x2', 'TVG': 'x3', 'TVPG': 'x4', 
			  'TV14': 'x5', 'TVMA': 'x6', 'TVNR': 'x7',
			  'Y7': 'x1', 'Y': 'x2', 'G': 'x3', 'PG': 'x4',
			  '14': 'x5', 'MA': 'x6', 'NR': 'x7', 'UNRATED': 'x7'}

MPAA_RATINGS = {'G': 'G1', 'PG': 'P2', 'PG-13': 'P3', 'PG13': 'P3',
				'R': 'R4', 'X': 'X5', 'NC-17': 'N6', 'NC17': 'N6',
				'NR': 'N8', 'UNRATED': 'N8'}

STAR_RATINGS = {'1': 'x1', '1.5': 'x2', '2': 'x3', '2.5': 'x4',
				'3': 'x5', '3.5': 'x6', '4': 'x7',
				'*': 'x1', '**': 'x3', '***': 'x5', '****': 'x7'}

HUMAN = {'mpaaRating': {'G1': 'G', 'P2': 'PG', 'P3': 'PG-13', 'R4': 'R',
						'X5': 'X', 'N6': 'NC-17', 'N8': 'Unrated'},
		 'tvRating': {'x1': 'TV-Y7', 'x2': 'TV-Y', 'x3': 'TV-G',
					  'x4': 'TV-PG', 'x5': 'TV-14', 'x6': 'TV-MA',
					  'x7': 'Unrated'},
		 'starRating': {'x1': '1', 'x2': '1.5', 'x3': '2', 'x4': '2.5',
						'x5': '3', 'x6': '3.5', 'x7': '4'}}

BOM = '\xef\xbb\xbf'

def tag_data(element, tag):
	for name in tag.split('/'):
		new_element = element.getElementsByTagName(name)
		if not new_element:
			return ''
		element = new_element[0]
	if not element.firstChild:
		return ''
	return element.firstChild.data

def _vtag_data(element, tag):
	for name in tag.split('/'):
		new_element = element.getElementsByTagName(name)
		if not new_element:
			return []
		element = new_element[0]
	elements = element.getElementsByTagName('element')
	return [x.firstChild.data for x in elements if x.firstChild]

def uniq(ilist) :
	olist = []
	for li in ilist:
		if li not in olist:
			olist.append(li)
	return olist

def from_text(full_path, mergefiles=True, mergelines=False, mergeparent=False):
	
	metadata = from_nfo(full_path)
	
	path, name = os.path.split(full_path)
	title, ext = os.path.splitext(name)

	filelist = []
	
	if mergefiles and mergeparent:
		sl = []
		dirs = path.split(os.path.sep)
		for i in range(len(dirs))[1:]:
			p = os.path.sep.join(dirs[:-i]+ ["default.txt"])
			if os.path.exists(p):
				sl = [p] + sl  #add to front of list
		filelist.extend(sl)

	filelist.extend([os.path.join(path, title) + '.properties',
					 os.path.join(path, '.meta', 'default.txt'),
					 os.path.join(path, 'default.txt'),
					 os.path.join(path, '.meta', name) + '.txt',
					 full_path + '.txt'])
	
	for metafile in filelist:
		if os.path.exists(metafile):
			if not mergefiles:
				metadata = {}
			prevkeys = metadata.keys()
			sep = ':='[metafile.endswith('.properties')]
			for line in file(metafile, 'U'):
				if line.startswith(BOM):
					line = line[3:]
				if line.strip().startswith('#') or not sep in line:
					continue
				key, value = [x.strip() for x in line.split(sep, 1)]
				if not key or not value:
					continue
				value = ''.join([x for x in value if ord(x) < 128])
				if key.startswith('v'):
					if key in metadata:
						metadata[key].append(value)
					else:
						metadata[key] = [value]
				else:
					if key in metadata:
						if key in prevkeys and mergelines:
							metadata[key] += ' ' + value
							prevkeys.remove(key)
						elif key in prevkeys:
							metadata[key] = value
							prevkeys.remove(key)
						elif mergelines:
							metadata[key] += ' ' + value
						else:
							metadata[key] = value
					else:
						metadata[key] = value

	for rating, ratings in [('tvRating', TV_RATINGS),
							('mpaaRating', MPAA_RATINGS),
							('starRating', STAR_RATINGS)]:
		x = metadata.get(rating, '').upper()
		if x in ratings:
			metadata[rating] = ratings[x]
			
	for k in metadata.keys():
		if k.startswith('v'):
			ulist = uniq(metadata[k])
			metadata[k] = ulist

	return metadata

def tag_data(element, tag):
    for name in tag.split('/'):
        found = False
        for new_element in element.childNodes:
            if new_element.nodeName == name:
                found = True
                element = new_element
                break
        if not found:
            return ''
    if not element.firstChild:
        return ''
    return element.firstChild.data

def _vtag_data_alternate(element, tag):
    elements = [element]
    for name in tag.split('/'):
        new_elements = []
        for elmt in elements:
            new_elements += elmt.getElementsByTagName(name)
        elements = new_elements
    return [x.firstChild.data for x in elements if x.firstChild]


def _nfo_vitems(source, metadata):

    vItems = {'vGenre': 'genre',
              'vWriter': 'credits',
              'vDirector': 'director',
              'vActor': 'actor/name'}

    for key in vItems:
        data = _vtag_data_alternate(source, vItems[key])
        if data:
            metadata.setdefault(key, [])
            for dat in data:
                if not dat in metadata[key]:
                    metadata[key].append(dat)

    if 'vGenre' in metadata:
        metadata['vSeriesGenre'] = metadata['vProgramGenre'] = metadata['vGenre']

    return metadata

def _parse_nfo(nfo_path, nfo_data=None):
    # nfo files can contain XML or a URL to seed the XBMC metadata scrapers
    # It's also possible to have both (a URL after the XML metadata)
    # pyTivo only parses the XML metadata, but we'll try to stip the URL
    # from mixed XML/URL files.  Returns `None` when XML can't be parsed.
    if nfo_data is None:
        nfo_data = [line.strip() for line in file(nfo_path, 'rU')]
    xmldoc = None
    try:
        xmldoc = minidom.parseString(os.linesep.join(nfo_data))
    except expat.ExpatError, err:
        if expat.ErrorString(err.code) == expat.errors.XML_ERROR_INVALID_TOKEN:
            # might be a URL outside the xml
            while len(nfo_data) > err.lineno:
                if len(nfo_data[-1]) == 0:
                    nfo_data.pop()
                else:
                    break
            if len(nfo_data) == err.lineno:
                # last non-blank line contains the error
                nfo_data.pop()
                return _parse_nfo(nfo_path, nfo_data)
    return xmldoc

def _from_tvshow_nfo(tvshow_nfo_path):
    items = {'description': 'plot',
             'title': 'title',
             'seriesTitle': 'showtitle',
             'starRating': 'rating',
             'tvRating': 'mpaa'}

    metadata = {}

    xmldoc = _parse_nfo(tvshow_nfo_path)
    if not xmldoc:
        return metadata

    tvshow = xmldoc.getElementsByTagName('tvshow')
    if tvshow:
        tvshow = tvshow[0]
    else:
        return metadata

    for item in items:
        data = tag_data(tvshow, items[item])
        if data:
            metadata[item] = data

    metadata = _nfo_vitems(tvshow, metadata)

    return metadata

def _from_episode_nfo(nfo_path, xmldoc):
    metadata = {}

    items = {'description': 'plot',
             'episodeTitle': 'title',
             'seriesTitle': 'showtitle',
             'originalAirDate': 'aired',
             'starRating': 'rating',
             'tvRating': 'mpaa'}

    # find tvshow.nfo
    path = nfo_path
    while True:
        basepath = os.path.dirname(path)
        if path == basepath:
            break
        path = basepath
        tv_nfo = os.path.join(path, 'tvshow.nfo')
        if os.path.exists(tv_nfo):
            metadata.update(_from_tvshow_nfo(tv_nfo))
            break

    episode = xmldoc.getElementsByTagName('episodedetails')
    if episode:
        episode = episode[0]
    else:
        return metadata

    metadata['isEpisode'] = 'true'
    for item in items:
        data = tag_data(episode, items[item])
        if data:
            metadata[item] = data

    season = tag_data(episode, 'displayseason')
    if not season or season == "-1":
        season = tag_data(episode, 'season')
    if not season:
        season = 1

    ep_num = tag_data(episode, 'displayepisode')
    if not ep_num or ep_num == "-1":
        ep_num = tag_data(episode, 'episode')
    if ep_num and ep_num != "-1":
        metadata['episodeNumber'] = "%d%02d" % (int(season), int(ep_num))

    if 'originalAirDate' in metadata:
        metadata['originalAirDate'] += 'T00:00:00Z'

    metadata = _nfo_vitems(episode, metadata)

    return metadata

def _from_movie_nfo(xmldoc):
    metadata = {}

    movie = xmldoc.getElementsByTagName('movie')
    if movie:
        movie = movie[0]
    else:
        return metadata

    items = {'description': 'plot',
             'title': 'title',
             'movieYear': 'year',
             'starRating': 'rating',
             'mpaaRating': 'mpaa'}

    metadata['isEpisode'] = 'false'

    for item in items:
        data = tag_data(movie, items[item])
        if data:
            metadata[item] = data

    metadata['movieYear'] = "%04d" % int(metadata.get('movieYear', 0))

    metadata = _nfo_vitems(movie, metadata)
    return metadata

def from_nfo(full_path):
    metadata = {}

    nfo_path = "%s.nfo" % os.path.splitext(full_path)[0]
    if not os.path.exists(nfo_path):
        return metadata

    xmldoc = _parse_nfo(nfo_path)
    if not xmldoc:
        return metadata

    if xmldoc.getElementsByTagName('episodedetails'):
        # it's an episode
        metadata.update(_from_episode_nfo(nfo_path, xmldoc))
    elif xmldoc.getElementsByTagName('movie'):
        # it's a movie
        metadata.update(_from_movie_nfo(xmldoc))

    # common nfo cleanup
    if 'starRating' in metadata:
        # .NFO 0-10 -> TiVo 1-7
        rating = int(float(metadata['starRating']) * 6 / 10 + 1.5)
        metadata['starRating'] = str(rating)

    for key, mapping in [('mpaaRating', MPAA_RATINGS),
                         ('tvRating', TV_RATINGS)]:
        if key in metadata:
            rating = mapping.get(metadata[key], None)
            if rating:
                metadata[key] = str(rating)
            else:
                del metadata[key]

    return metadata

def basic(full_path):
	base_path, name = os.path.split(full_path)
	title, ext = os.path.splitext(name)
	try:
		mtime = os.stat(full_path).st_mtime
	except:
		desc = "Error trying to stat " + full_path
		mtime = 0
	else:
		if (mtime < 0):
			mtime = 0
		desc = ""
		
	originalAirDate = datetime.fromtimestamp(mtime)

	metadata = {'title': title,
				'description': desc,
				'originalAirDate': originalAirDate.isoformat()}

	return metadata

def dump(output, metadata):
	for key in metadata:
		if key.startswith("__"): continue
		value = metadata[key]
		if type(value) == list:
			for item in value:
				output.write('%s : %s\n' % (key, item.encode('utf-8')))
		else:
			if key in HUMAN and value in HUMAN[key]:
				output.write('%s : %s\n' % (key, HUMAN[key][value]))
			else:
				output.write('%s : %s\n' % (key, value.encode('utf-8')))

