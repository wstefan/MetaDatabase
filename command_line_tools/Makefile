# install command line tools
install_dir=/opt/metadbtools
mysql_server = 172.30.205.56
mysql_db = redmine_default
mysql_user = metauser
mysql_password = 8hO1jKO8Vj3s23l
bin_dir = /usr/bin
python_dir = /usr/bin/python

install: 
	mkdir -p $(install_dir)
	# copy files to install dir
	cp metadata.py $(install_dir)
	cp metadbtools.py* $(install_dir)
	cp metasearch.py $(install_dir)
	# create config file
	echo "# Config file for meta data database" > /etc/metadbconfig.cfg
	echo "mysql_server = " $(mysql_server) >> /etc/metadbconfig.cfg
	echo "mysql_db = " $(mysql_db) >> /etc/metadbconfig.cfg
	echo "mysql_user = " $(mysql_user) >> /etc/metadbconfig.cfg
	echo "mysql_password = " $(mysql_password) >> /etc/metadbconfig.cfg
	# create shell scripts to run command line tools
	echo "#!/bin/bash" > $(bin_dir)/metasearch
	echo $(python_dir) $(install_dir)"/metasearch.py $*" >> $(bin_dir)/metasearch
	chmod a+x $(bin_dir)/metasearch
	echo "#!/bin/bash" > $(bin_dir)/metadata
	echo $(python_dir) $(install_dir)"/metadata.py $*" >> $(bin_dir)/metadata
	chmod a+x $(bin_dir)/metadata
