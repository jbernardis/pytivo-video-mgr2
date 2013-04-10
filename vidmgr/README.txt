PyTivo Video Manager - Version 2.0  README.txt

see changelog.txt for a history of changes

what it is
==========

PyTivo video manager (vidmgr) is an HME application that allows you to request that videos in your 
library be "Pushed" to your tivo instead of the normal pull.  Since it's an HME app, this request
can be made from your easy chair with your tivo remote.  Pushing allows videos that are in a
compatible MP4 format to be transferred as is - saving time and space - instead of the transcoding
that a pull will always cause (although a push can also be requested for a video format that requires
transcoding).  vidmgr can also be used to delete videos from your library.

Version 2.0 is a complete rewrite of the application with better, more object-oriented code.  Among the
improvements that will be visible to users:
	1.) The video information is obtained from a cache instead of being read from the disk.  The cache
	    can be built when the program starts up, or ahead of time - at your choice.  The advantage of
	    building the cache ahead of time is that you can get more complex in terms of the way the 
	    cache is built (you can still build a complex cache at thread start time if you are willing to
	    tolerate a delay - my ARM based NAS builds the cache for my 400 video library in about 5 seconds.
	    The cache supports the ability to create "virtual" shares that are based on metadata, including any
	    metadata that you may have added yourself.  So, for example, you can create a "virtual" share for
	    John Wayne movies, or you can have a virtual share that breaks the videos down my genre.
	    
	2.) You now have the ability to change options on a directory by directory (or virtual share) basis.
	    You want this  directory sorted on episode number and that one sorted on show title - no problem.
	    Sorting can now be done based on ANY combinations of strings from the metadata.  You can also control
	    the display "name" for a video file based on the directory (or virtual share).
	    
    3.) the user interface was cleaned up - there is no longer a menu choice for push/delete.  Pushing is
        accomplished by pressing the select button - if you have multiple tivos a dialog box will pop-up
        over the display so you can choose the proper target.  Delete is accomplished by pressing clear.  
        Again, a dialog box will pop-up asking for confirmation.
        
There are many other changes as well, but they are more subtle and/or are not visible to a user.

There is one limitation over the original program - This is for HD only.  If the application finds that
your tivo does not support an HD resolution, it simply exits.  One implication of this - if you plan on 
retaining any of your HD files from the previous version of Vidmgr, then the "HD" needs to be removed
from the file name.

vidmgr is a TiVo HME application designed to operate under wmcbrine's hme for python
framework.  It is NOT a stand-alone application.  Please install the pyhme package (I have tested with version 0.19)
and make sure it is running before you install vidmgr.

Vidmgr is designed to operate in conjunction with the PyTivo transcoding server - If you are not 
using pytivo, then there is no point in installing vidmgr.  I have tested vidmgr with the mcbrine
fork of pytivo.  I am not familiar with the other forks to know whether or not it will run there.

====================================================================================================

installation/setup
==================

If you've gotten this far, you must want to install this.  It's very simple:

1. Go to the directory where you have pyhme installed.  There should be a lot of subdirectories here,
one per application.  Create a new directory here named "vidmgr"

2. Copy the contents of the vidmgr directory tree from this package into this new directory.  This should
include several .py files, a .png file, 2 .dist files, README.txt, and a directory named skins.  Within the
skins directory, there will be a collection of .png files.   

3. Configure - you will need to add vidmgr to the list of applications that are launched by pyhme.  See
the pyhme documentation for how to do this.   You will also need to set up your vidmgr.ini file (in the vidmgr
directory) and the .vidmgr.ini files in the various video directories as you wish.

Note - this is a difference from vidmgr 1.0.  vidmgr no longer uses the pyhme config.ini file to hold
its configuration information.  Instead everything goes into vidmgr.ini and the satellite .vidmgr.ini files.
Contained with the distribution is a vidmgr.ini.dist file.  This file is heavily documented with all of
the possible options and their default and possible values.  Follow the directions in this file.

The distribution also contains a .vidmgr.ini.dist file.  This is a satellite file - it goes directly in
the directory structure where you store your video files.  These files can be used to change certain
options for that directory and the directories below it.  Please see the .dist file for a complete list
of the allowed options and values.

=======================================================================================================

Moving from Version 1 to Version 2
==================================

To move from version 1 to version 2, the basic instruction is to just start new.  There ARE a few
files that can move straight from 1 to 2 though:

1) thumbs.cache - this is the cache file for video artwork.  If you move this into the version 2
directory, you save yourself from having to regenerate it, but since it is regenerated on the
fly, there is no great benefit to moving it.  It's really up to you.

2) skins - version 1.0 had ALL png files - even the standard ones, under a subdirectory in the skins
directory.  The new approach is to have the default png files directly in the skins directory, and then
to have subdirectories below this point contain user skins.  By default, the value of skin is set to 
None, but if you set it to the name of a subdirectory, vidmgr will look in thei subdirectory FIRST
before it then looks directly in the skins directory.  This means that you do NOT need to copy
png files that you are NOT changing.  Also note - this version of vidmgr is for HD only.  As such,
files with HD in their names no longer need this - remove the HD.  This means, of course, that the
name will conflict with the SD file name, but you no longer need the SD name.

3) config.ini/vidmgr.ini - vidmgr no longer looks in config.ini for any configuration information.
Any information you had there needs to be moved into vidmgr.ini in the vidmgr directory.  PLEASE
read the vidmgr.ini.dist file that came with this distribution - it is heavily commented with
how to set all of the various options.  Of particular significance when moving form version 1 to
version 2 are the sort and display options.

=======================================================================================================

Usage
=====

Vidmgr presents a directory tree to you.  You can step into and out of directories using the normal
tivo navigation keys.  The root directory of this tree is controlled by how you build your cache - see below.

while browsing this tree, you can also navigate using the number keys.  1 takes you 10% of the
way through the list, 5 = 50%, 7 = 70%, etc.  0 alternately takes you to the end of the list and then to the
beginning of the list

Vidmgr will also show video artwork on the right hand side of the screen.  Vidmgr looks for
the following file:  <full-video-file-name-including-extension>.jpg or, if this doesn't exist, folder.jpg.
The view into which this graphic is placed is 620 pixels wide by 450 pixels high.  If your graphic exceeds
those dimensions it will be scaled while maintaining the aspect ratio.  Folder.jpg will also be the thumbnail
used for the enclosing folder or share.  Also, if there is a folder.txt file in a directory, or in the
subtending .meta directory, its contents - notably the description field will be shown on the display
above the thumbnail.

Vidmgr ALSO will show artwork for physical shares, virtual shares and virtual directories created within virtual shares.
For physical shares, place a file named "share.jpg" in the root directory of the share.  For virtual shares and for
the virtual directories within them, jpg files are placed under the vidmgr directory in a subdirectory names "artwork".  The
actual file names are based on the Share name and/or the metadata values that are used to group them.  Because metadata
can basically contain anything, including characters that are not permissible in file names, there is some processing that
goes on to make sure the file names are valid.  It's pretty straight-forward, but to find out EXACTLY what filename vidmgr
is looking for, run BuildCache.py with the verbose option ("python BuildCache.py -v") and it will show you, for EVERY virtual
share and metadata value it finds what filename it is looking for.  After you learn the algorithm, you shouldn't need to do this
anymore, but it's there just in case.

For dvdvideo shares, vidmgr is totally dependent on accurate metadata.  Metadata (and thumbnails) all belong
in the directory containing the VIDEO_TS directory or in a subtending .meta directory.  Metadata is processed
as follows.  default.txt contains the DVD metadata.  __Txx.mpg.txt contains the metadata for title xx.  The
title-specific metadata is overlaid on top of the DVD metadata according to the metamergefiles and metamergefiles
configuration parameters.  The thumbnail for the DVD is in a file named folder.jpg.  In addition, it is
possible to have a thumbnail for a specific title;  the name should be __Txx.mpg.jpg.  If there is no metadata
for a dvdvideo share, vidmgr assumes that there is only 1 title, and its title is the directory name.

If you press select while on a video file, you will initiate the push operation.  If you only have one tivo, the
file will simply be pushed.  If you have multiple tivos, a pop-up menu will ask you to choose the proper target.

If you are positioned on a video file and press clear, you will have initiated the delete operation.  If deletes
are not allowed or if this is a dvd video, you will simply receive a BONK sound.  Otherwise, you will be asked to
press thumbs-up to confirm and when you do, the file and its associated metadata and artwork will be deleted.  Note
the folder-level metadata or artwork (folder.jpg, default.txt) will NOT be deleted.  If you press ANYTHING other
than thumbs-up, the delete is cancelled.  The following video files cannot be deleted: 1) those for which deleteallowed
is set to false, 2) any video that is part of a DVD since these are virtual files constructed on the fly from the VOB
files, and 3) videos that have multiple file system links since vidmgr cannot follow these links to make sure that
all references are properly updated.

At any time on any list you can press the info button to see a complete list of the metadata.  You can control
which metadata items appear at the front of this display and which are ignored with configuration options.  On
the info display, you can press left, clear, or info to return to the screen you came from.  If the information
does not fit on one page, you will see paging cues and you can use either up/down or channel up/down to traverse
the pages.

=======================================================================================================

Building The Cache
==================

When the application first receives control, it will attempt to open the cache.  If it does not find it, it will attempt 
to build it dynamically.  Depending on the size of your video library, this could take some time - so you may want to
build it ahead of time.  To build the cache yourself, simply change into the vidmgr directory and run the following
command: "python BuildCache.py".  If thereafter you want to go back to dynamically built caches, delete the file 
"video.cache" from the same directory.  You can specify the -v (verbose) option on the command line to get a little
additional information about the cache building process (i.e. "python BuildCache.py -v")

If the cache is built dynamically, it is NEVER written back to disk.  This way, each time you start up, it will be rebuilt.

If the cache if built ahead of time, it will be written back to disk at program exit if it has changed.  Basically this
means if you have deleted a video, since this is the only change possible through the HME interface.  If you build 
your cache ahead of time, you are responsible for keeping it up to date as you add/delete videos.  This is the way
mine is configured, and I rebuild my cache each night through a cron job.

As a convenience, you can also trigger a rebuild of the cache with the remote control by hitting Thumbs-Down three
times in succession.  The app will be non-responsive while the cache is rebuilding.  After it is done, it will
restart at the top of the tree.

Vidmgr.ini contains some options for controlling how the Cache is built.  Please refer to the dist file for more information.

Vidmgr.ini is also where you define your virtual shares.  Again - please consult the dist file for documentation about
virtual shares.
