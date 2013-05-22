SRC = *.py icon.png
SKN = skins/*.png

all: install 

install : .installpy .installskin

.installpy : $(SRC)
	mkdir -p /usr/local/pyhme/vidmgr
	cp $? /usr/local/pyhme/vidmgr
	touch .installpy

.installskin : $(SKN)
	mkdir -p /usr/local/pyhme/vidmgr/skins
	cp $? /usr/local/pyhme/vidmgr/skins
	touch .installskin

