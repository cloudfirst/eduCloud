# /bin/bash

sudo dpkg -i educloud-core_*_all.deb
sudo dpkg -i educloud-webbase_*_all.deb 
sudo dpkg -i educloud-clc_*_all.deb
sudo dpkg -i educloud-portal_*_all.deb
sudo dpkg -i educloud-walrus_*_all.deb
sudo dpkg -i educloud-virtapp_*_all.deb
sudo dpkg -i educloud-cc_*_all.deb
sudo dpkg -i educloud-bizrule_*_all.deb
sudo dpkg -i nodedaemon-clc_*_all.deb
sudo dpkg -i nodedaemon-walrus_*_all.deb
sudo dpkg -i nodedaemon-cc_*_all.deb
sudo dpkg -i nodedaemon-nc_*_all.deb

sudo chown -R luhya:luhya /usr/local/www
sudo chown -R luhya:luhya /usr/local/nodedaemon
sudo chown -R luhya:luhya /usr/local/webconfig

mkdir tmp
tar vxf pip.tar -C ./tmp/
cd ./tmp
sudo pip install Django-*.tar.gz
sudo pip install IPy-*.tar.gz
sudo pip install MySQL-python-*.tar.gz
sudo pip install amqp-*.tar.gz
sudo pip install business-rules-*.tar.gz
sudo pip install linux-metrics-*.tar.gz
sudo pip install luhyaapi-*.tar.gz
sudo pip install netifaces-*.tar.gz
sudo pip install pexpect-*.tar.gz
sudo pip install pika-*.tar.gz
sudo pip install psutil-*.tar.gz
sudo pip install python-iptables-*.tar.gz
sudo pip install python-memcached-*.tar.gz
sudo pip install pyzmq-*.tar.gz
sudo pip install requests-*.tar.gz
sudo pip install sortedcontainers-*.tar.gz
sudo pip install structlog-*.tar.gz
