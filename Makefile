# Makefile
#
#

.PHONY: build clean

EDU_CORE        =debian/educloud-core
EDU_WEBBASE     =debian/educloud-webbase

WEB_PORTAL      =debian/educloud-portal
WEB_CLC         =debian/educloud-clc
WEB_WALRUS      =debian/educloud-walrus
WEB_CC          =debian/educloud-cc
WEB_VIRTAPP     =debian/educloud-virtapp
WEB_BIZRULE     =debian/educloud-bizrule

DAEMON_CLC      =debian/nodedaemon-clc
DAEMON_WALRUS   =debian/nodedaemon-walrus
DAEMON_CC       =debian/nodedaemon-cc
DAEMON_NC       =debian/nodedaemon-nc
DAEMON_TNC	=debian/nodedaemon-tnc

build:
	echo "now is building educloud debian packages ... ... "
clean:
	echo "now is cleaning educloud debian packages ... ... "
	rm -fr $(EDU_CORE) $(EDU_WEBBASE) $(WEB_PORTAL) $(WEB_CLC) $(WEB_WALRUS) $(WEB_CC) $(WEB_VIRTAPP) $(WEB_BIZRULE) || true
	rm -fr $(DAEMON_CLC) $(DAEMON_WALRUS) $(DAEMON_CC) $(DAEMON_NC) || true
	rm debian/*.debhelper.log debian/*.substvars  debian/files debian/stamp* debian/compat || true
	find ./nodeDaemon -name *.spec -delete || true
	rm webconfig/serverTools/recoverVMfromCrash.spec || true
	rm webconfig/piplib/3rd/luhyaapi-*.tar.gz || true
	rm ../*.deb ../pip.tar || true
publish:
	rm $(CURDIR)/../AutoITManagement/playbook/roles/allinone-ndp/files/educloud*.deb || true
	rm $(CURDIR)/../AutoITManagement/playbook/roles/allinone-ndp/files/nodedaemon*.deb || true
	rm $(CURDIR)/../AutoITManagement/playbook/roles/allinone-ndp/files/pip.tar || true
	cp $(CURDIR)/../*.deb   $(CURDIR)/../AutoITManagement/playbook/roles/allinone-ndp/files/
	cp $(CURDIR)/../pip.tar $(CURDIR)/../AutoITManagement/playbook/roles/allinone-ndp/files
	rm $(CURDIR)/webconfig/upgrade/educloud*.deb || true
	rm $(CURDIR)/webconfig/upgrade/nodedaemon*.deb || true
	rm $(CURDIR)/webconfig/upgrade/pip.tar || true
	cp ../*.deb   $(CURDIR)/webconfig/upgrade/
	cp ../pip.tar $(CURDIR)/webconfig/upgrade/
	cd $(CURDIR)/webconfig/ && tar -zcvf /tmp/upgrade.tar.gz upgrade/
install:
	####################
	#     LUHYA API    #
	####################
	cd $(CURDIR)/webconfig/piplib/sharelib/educloud-luhyaapi && python setup.py sdist
	cp $(CURDIR)/webconfig/piplib/sharelib/educloud-luhyaapi/dist/*.tar.gz  $(CURDIR)/webconfig/piplib/3rd/
	rm -fr $(CURDIR)/webconfig/piplib/sharelib/educloud-luhyaapi/dist
	cd $(CURDIR)/webconfig/piplib/3rd/ && tar cvf $(CURDIR)/../pip.tar *.gz *.deb

	####################
	#     EDU_CORE     #
	####################
	install -d $(EDU_CORE)/etc/educloud/modules
	touch $(EDU_CORE)/etc/educloud/modules/core
	cp $(CURDIR)/debian/educloud.conf                    $(EDU_CORE)/etc/educloud/modules/

	install -d $(EDU_CORE)/usr/local/webconfig
	cp    $(CURDIR)/debian/fuse.conf                       $(EDU_CORE)/usr/local/webconfig/
	cp    $(CURDIR)/debian/sudoers                         $(EDU_CORE)/usr/local/webconfig/
	cp    $(CURDIR)/debian/afterboot.py                    $(EDU_CORE)/usr/local/webconfig/
	cp -r $(CURDIR)/webconfig/rsync                        $(EDU_CORE)/usr/local/webconfig/

	#####################
	#     EDU_WEBBASE   #
	#####################
	install -d $(EDU_WEBBASE)/usr/local/www/luhyacloud/
	cp $(CURDIR)/luhyacloud/*.py                         $(EDU_WEBBASE)/usr/local/www/
	python -m compileall $(CURDIR)/luhyacloud/luhyacloud/
	mv $(CURDIR)/luhyacloud/luhyacloud/*.pyc             $(EDU_WEBBASE)/usr/local/www/luhyacloud/
	#cp $(CURDIR)/luhyacloud/luhyacloud/*.py             $(EDU_WEBBASE)/usr/local/www/luhyacloud/
	cp $(CURDIR)/luhyacloud/luhyacloud/wsgi.py           $(EDU_WEBBASE)/usr/local/www/luhyacloud/
	rm $(EDU_WEBBASE)/usr/local/www/luhyacloud/wsgi.pyc

	install -d $(EDU_WEBBASE)/usr/local/webconfig/
	cp -r $(CURDIR)/webconfig/apache2                    $(EDU_WEBBASE)/usr/local/webconfig/


	#####################
	#     WEB_PORTAL    #
	#####################
	install -d $(WEB_PORTAL)/etc/educloud/modules
	touch $(WEB_PORTAL)/etc/educloud/modules/portal

	install -d $(WEB_PORTAL)/usr/local/www/portal
	python -m compileall $(CURDIR)/luhyacloud/portal/
	mv $(CURDIR)/luhyacloud/portal/*.pyc                $(WEB_PORTAL)/usr/local/www/portal/
	#cp $(CURDIR)/luhyacloud/portal/*.py		    $(WEB_PORTAL)/usr/local/www/portal/
	cp -r $(CURDIR)/luhyacloud/portal/conf              $(WEB_PORTAL)/usr/local/www/portal/
	cp -r $(CURDIR)/luhyacloud/portal/static            $(WEB_PORTAL)/usr/local/www/portal/
	cp -r $(CURDIR)/luhyacloud/portal/templates         $(WEB_PORTAL)/usr/local/www/portal/

	##################
	#     WEB_CLC    #
	##################
	install -d $(WEB_CLC)/etc/educloud/modules
	touch $(WEB_CLC)/etc/educloud/modules/clc

	install -d $(WEB_CLC)/usr/local/www/clc
	python -m compileall $(CURDIR)/luhyacloud/clc/
	mv $(CURDIR)/luhyacloud/clc/*.pyc                   $(WEB_CLC)/usr/local/www/clc/
	#cp $(CURDIR)/luhyacloud/clc/*.py		            $(WEB_CLC)/usr/local/www/clc/

	cp -r $(CURDIR)/luhyacloud/clc/conf                 $(WEB_CLC)/usr/local/www/clc/
	cp -r $(CURDIR)/luhyacloud/clc/static               $(WEB_CLC)/usr/local/www/clc/
	cp -r $(CURDIR)/luhyacloud/clc/templates            $(WEB_CLC)/usr/local/www/clc/
	cp -r $(CURDIR)/luhyacloud/clc/sql                  $(WEB_CLC)/usr/local/www/clc/

	#####################
	#     WEB_WALRUS    #
	#####################
	install -d $(WEB_WALRUS)/etc/educloud/modules
	touch $(WEB_WALRUS)/etc/educloud/modules/walrus

	install -d $(WEB_WALRUS)/usr/local/www/walrus
	python -m compileall $(CURDIR)/luhyacloud/walrus/
	mv $(CURDIR)/luhyacloud/walrus/*.pyc                $(WEB_WALRUS)/usr/local/www/walrus/
	#cp $(CURDIR)/luhyacloud/walrus/*.py		        $(WEB_WALRUS)/usr/local/www/walrus/

	#################
	#     WEB_CC    #
	#################
	install -d $(WEB_CC)/etc/educloud/modules
	touch $(WEB_CC)/etc/educloud/modules/cc

	install -d $(WEB_CC)/usr/local/www/cc
	python -m compileall $(CURDIR)/luhyacloud/cc/
	mv $(CURDIR)/luhyacloud/cc/*.pyc                     $(WEB_CC)/usr/local/www/cc/
	#cp $(CURDIR)/luhyacloud/cc/*.py                     $(WEB_CC)/usr/local/www/cc/

	######################
	#     WEB_VIRTAPP    #
	######################
	install -d $(WEB_VIRTAPP)/etc/educloud/modules
	touch $(WEB_VIRTAPP)/etc/educloud/modules/virtapp

	install -d $(WEB_VIRTAPP)/usr/local/www/virtapp
	python -m compileall $(CURDIR)/luhyacloud/virtapp/
	mv $(CURDIR)/luhyacloud/virtapp/*.pyc                    $(WEB_VIRTAPP)/usr/local/www/virtapp/
	#cp $(CURDIR)/luhyacloud/virtapp/*.py                    $(WEB_VIRTAPP)/usr/local/www/virtapp/

	cp -r $(CURDIR)/luhyacloud/virtapp/conf                  $(WEB_VIRTAPP)/usr/local/www/virtapp/
	cp -r $(CURDIR)/luhyacloud/virtapp/templates             $(WEB_VIRTAPP)/usr/local/www/virtapp/
	cp -r $(CURDIR)/luhyacloud/virtapp/sql                   $(WEB_VIRTAPP)/usr/local/www/virtapp/

	######################
	#     WEB_BIZRULE    #
	######################
	install -d $(WEB_BIZRULE)/etc/educloud/modules
	touch $(WEB_BIZRULE)/etc/educloud/modules/bizrule

	install -d $(WEB_BIZRULE)/usr/local/www/bizrule
	python -m compileall $(CURDIR)/luhyacloud/bizrule/
	mv $(CURDIR)/luhyacloud/bizrule/*.pyc                    $(WEB_BIZRULE)/usr/local/www/bizrule/
	#cp $(CURDIR)/luhyacloud/bizrule/*.py                    $(WEB_BIZRULE)/usr/local/www/bizrule/

	cp -r $(CURDIR)/luhyacloud/bizrule/conf                  $(WEB_BIZRULE)/usr/local/www/bizrule/
	cp -r $(CURDIR)/luhyacloud/bizrule/templates             $(WEB_BIZRULE)/usr/local/www/bizrule/
	cp -r $(CURDIR)/luhyacloud/bizrule/static                $(WEB_BIZRULE)/usr/local/www/bizrule/
	cp -r $(CURDIR)/luhyacloud/bizrule/sql                   $(WEB_BIZRULE)/usr/local/www/bizrule/

	##################################################
	# when use pyinstaller to compile exeutable file,
	# you must set dpkg-buildflags to avoid strip.
	# before run dpkg-buildpackage, set
	#   export  DEB_BUILD_OPTIONS="nostrip noopt"
	##################################################

	#####################
	#     DAEMON_CLC    #
	#####################
	install -d $(DAEMON_CLC)/usr/local/nodedaemon/clc
	cd $(CURDIR)/nodeDaemon/clc && sudo -u luhya pyinstaller clc_status_consumer.py -F -s
	cp $(CURDIR)/nodeDaemon/clc/dist/clc_status_consumer         $(DAEMON_CLC)/usr/local/nodedaemon/clc

	cd $(CURDIR)/nodeDaemon/clc && sudo -u luhya pyinstaller clc_cmd_consumer.py -F -s
	cp $(CURDIR)/nodeDaemon/clc/dist/clc_cmd_consumer         $(DAEMON_CLC)/usr/local/nodedaemon/clc

	install -d $(DAEMON_CLC)/etc/supervisor/conf.d
	cp $(CURDIR)/nodeDaemon/clc/supervisor/nodedaemon-clc.conf   $(DAEMON_CLC)/etc/supervisor/conf.d

	########################
	#     DAEMON_WALRUS    #
	########################
	install -d $(DAEMON_WALRUS)/usr/local/nodedaemon/walrus

	cd $(CURDIR)/nodeDaemon/walrus && sudo -u luhya pyinstaller walrus_status_publisher.py -F -s
	cp $(CURDIR)/nodeDaemon/walrus/dist/walrus_status_publisher            $(DAEMON_WALRUS)/usr/local/nodedaemon/walrus

	install -d $(DAEMON_WALRUS)/etc/supervisor/conf.d
	cp $(CURDIR)/nodeDaemon/walrus/supervisor/nodedaemon-walrus.conf   $(DAEMON_WALRUS)/etc/supervisor/conf.d

	####################
	#     DAEMON_CC    #
	####################
	install -d $(DAEMON_CC)/usr/local/nodedaemon/cc

	cd $(CURDIR)/nodeDaemon/cc && sudo -u luhya pyinstaller cc_cmd_consumer.py -F -s
	cd $(CURDIR)/nodeDaemon/cc && sudo -u luhya pyinstaller cc_rpc_server.py -F -s
	cd $(CURDIR)/nodeDaemon/cc && sudo -u luhya pyinstaller cc_status_consumer.py -F -s
	cd $(CURDIR)/nodeDaemon/cc && sudo -u luhya pyinstaller cc_status_publisher.py -F -s
	cp $(CURDIR)/nodeDaemon/cc/dist/cc_*            $(DAEMON_CC)/usr/local/nodedaemon/cc

	install -d $(DAEMON_CC)/etc/supervisor/conf.d
	cp $(CURDIR)/nodeDaemon/cc/supervisor/nodedaemon-cc.conf   $(DAEMON_CC)/etc/supervisor/conf.d

	####################
	#     DAEMON_NC    #
	####################
	install -d $(DAEMON_NC)/etc/educloud/modules
	touch $(DAEMON_NC)/etc/educloud/modules/nc

	install -d $(DAEMON_NC)/usr/local/nodedaemon/nc

	cd $(CURDIR)/nodeDaemon/nc && sudo -u luhya pyinstaller nc_cmd_consumer.py -F -s
	cd $(CURDIR)/nodeDaemon/nc && sudo -u luhya pyinstaller nc_status_publisher.py -F -s
	cd $(CURDIR)/nodeDaemon/nc && sudo -u luhya pyinstaller nc_sshfs.py -F -s
	cp $(CURDIR)/nodeDaemon/nc/dist/nc_*            $(DAEMON_NC)/usr/local/nodedaemon/nc/

	install -d $(DAEMON_NC)/etc/supervisor/conf.d
	cp $(CURDIR)/nodeDaemon/nc/supervisor/nodedaemon-nc.conf   $(DAEMON_NC)/etc/supervisor/conf.d/

	##
	## add tool for host crash recovery
	##
	install -d $(DAEMON_NC)/usr/local/bin
	cd $(CURDIR)/webconfig/serverTools/ && sudo -u luhya pyinstaller recoverVMfromCrash.py -F -s
	cp $(CURDIR)/webconfig/serverTools/dist/recoverVMfromCrash             $(DAEMON_NC)/usr/local/bin/
