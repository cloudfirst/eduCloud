# /bin/bash

sudo dpkg -i nodedaemon-nc_*_all.deb

sudo chown -R luhya:luhya /usr/local/nodedaemon
sudo chown -R luhya:luhay /usr/local/webconfig

mkdir tmp
tar vxf pip.tar -C ./tmp/
cd ./tmp
sudo pip install IPy-*.tar.gz
sudo pip install linux-metrics-*.tar.gz
sudo pip install netifaces-*.tar.gz
sudo pip install pexpect-*.tar.gz
sudo pip install pika-*.tar.gz
sudo pip install psutil-*.tar.gz
sudo pip install pyzmq-*.tar.gz
sudo pip install requests-*.tar.gz
sudo pip install sortedcontainers-*.tar.gz
sudo pip install structlog-*.tar.gz
