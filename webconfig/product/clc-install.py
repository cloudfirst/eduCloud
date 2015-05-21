import os, commands, sys
import time

DST_IP = '192.168.56.103'

def checkPackage( pname ):
    cmd_line = 'dpkg -l | grep %s' % pname
    output = commands.getoutput(cmd_line)
    if len(output) > 0 and output.split()[0] == 'ii':
       return True
    else:
       return False

##############################################################################
# 1. update /etc/apt/sources.list
##############################################################################
if not os.path.exists('/etc/apt/sources.list.luhya'):
    cmd_line = 'sudo cp /etc/apt/sources.list /etc/apt/sources.list.luhya'
    commands.getoutput(cmd_line)

    cmd_line = 'cp /etc/apt/sources.list /tmp/'
    commands.getoutput(cmd_line)

    with open('/tmp/sources.list', 'a') as myfile:
        myfile.write('\ndeb http://%s/debian/ zhejiang non-free' % DST_IP)

    cmd_line = 'sudo cp /tmp/sources.list /etc/apt/sources.list'
    commands.getoutput(cmd_line)

##############################################################################
# 2. Import the repository's public key
##############################################################################
cmd_line = 'apt-key list | grep luhya'
ret = commands.getoutput(cmd_line)
if ret == '':
    cmd_line = 'curl http://%s/packages.educloud.key > /tmp/packages.educloud.key' % DST_IP
    commands.getoutput(cmd_line)
    cmd_line = 'sudo apt-key add /tmp/packages.educloud.key'
    commands.getoutput(cmd_line)

##############################################################################
# 3. Fetch the list of packages available at the new source
##############################################################################
cmd_line = 'sudo rm /var/lib/apt/lists/*'
os.system(cmd_line)
cmd_line = 'sudo rm /var/lib/apt/lists/partial/*'
os.system(cmd_line)
cmd_line = 'sudo apt-get update'
os.system(cmd_line)

##############################################################################
# 4. install mysql-server without password prompt
##############################################################################
with open('/tmp/mysql-server.list', 'w') as myfile:
    myfile.write('mysql-server mysql-server/root_password password root\n')
    myfile.write('mysql-server mysql-server/root_password_again password root\n')

cmd_line = 'sudo debconf-set-selections /tmp/mysql-server.list'
commands.getoutput(cmd_line)

cmd_line = 'sudo apt-get -y install mysql-server'
os.system(cmd_line)

if checkPackage('mysql-server-5.5') == False:
   print "--------------------------------------------------"
   print "Install mysql-server-5.5 Failed, please try again."
   print "--------------------------------------------------"
   exit(1)

##############################################################################
# 5. create a user named luhya
##############################################################################
cmd_line = 'sudo cut -d: -f1 /etc/passwd | grep luhya'
ret = commands.getoutput(cmd_line)
if ret == '':
    cmd_line = 'sudo useradd  -m -s /bin/bash -U luhya'
    commands.getoutput(cmd_line)

##############################################################################
# 6. create /storage directories and download data.vdi
##############################################################################
if not os.path.exists('/var/log/educloud'):
    os.system('sudo mkdir -p /var/log/educloud')
if not os.path.exists('/storage'):
    os.system('sudo mkdir /storage')
if not os.path.exists('/storage/images'):
    os.system('sudo mkdir -p /storage/images')
    os.system('sudo mkdir -p /storage/VMs')
    os.system('sudo mkdir -p /storage/config')
    os.system('sudo mkdir -p /storage/space')
if not os.path.exists('/storage/space/software'):
    os.system('sudo mkdir -p /storage/space/software')
    os.system('sudo mkdir -p /storage/space/pub-data ')
    os.system('sudo mkdir -p /storage/space/prv-data')
    os.system('sudo mkdir -p /storage/space/database')
if not os.path.exists('/storage/space/prv-data/luhya'):
    os.system('sudo mkdir -p /storage/space/prv-data/luhya')
if not os.path.exists('/storage/space/database/images'):
    os.system('sudo mkdir -p /storage/space/database/images')
    os.system('sudo mkdir -p /storage/space/database/instances')
if not os.path.exists('/storage/tmp'):
    os.system('sudo mkdir -p /storage/tmp')
if not os.path.exists('/storage/tmp/images'):
    os.system('sudo mkdir -p /storage/tmp/images')
    os.system('sudo mkdir -p /storage/tmp/VMs')

cmd_line = 'cd /tmp && wget http://%s/database.vdi' % DST_IP
os.system(cmd_line)
cmd_line = 'sudo mv /tmp/database.vdi /storage/images/database'
os.system(cmd_line)

cmd_line = 'cd /tmp && wget http://%s/data.vdi' % DST_IP
os.system(cmd_line)
cmd_line = 'sudo mv /tmp/data.vdi /storage/images/data'
os.system(cmd_line)

##############################################################################
# 7. install educloud in one machine by apt-get
##############################################################################
cmd_line = 'sudo apt-get -y install educloud-core educloud-portal educloud-clc educloud-walrus nodedaemon-clc nodedaemon-walrus'
os.system(cmd_line)

cmd_line = 'sudo rm /var/cache/apt/archives/*.deb'
os.system(cmd_line)

# verify deb package install status
if checkPackage('educloud-core') == False:
   print "--------------------------------------------------"
   print "Install educloud-core Failed, please try again."
   print "--------------------------------------------------"
   exit(1)
if checkPackage('educloud-portal') == False:
   print "--------------------------------------------------"
   print "Install educloud-portal Failed, please try again."
   print "--------------------------------------------------"
   exit(1)
if checkPackage('educloud-clc') == False:
   print "--------------------------------------------------"
   print "Install educloud-clc Failed, please try again."
   print "--------------------------------------------------"
   exit(1)
if checkPackage('educloud-walrus') == False:
   print "--------------------------------------------------"
   print "Install educloud-walrus Failed, please try again."
   print "--------------------------------------------------"
   exit(1)
if checkPackage('nodedaemon-clc') == False:
   print "--------------------------------------------------"
   print "Install nodedaemon-clc Failed, please try again."
   print "--------------------------------------------------"
   exit(1)
if checkPackage('nodedaemon-walrus') == False:
   print "--------------------------------------------------"
   print "Install nodedaemon-walrus Failed, please try again."
   print "--------------------------------------------------"
   exit(1)

# install vbox ext pack
cmd_line = 'wget http://%s/Oracle_VM_VirtualBox_Extension_Pack-4.3.20-96996.vbox-extpack' % DST_IP
os.system(cmd_line)

cmd_line = 'sudo vboxmanage extpack install Oracle_VM_VirtualBox_Extension_Pack-4.3.20-96996.vbox-extpack'
os.system(cmd_line)

cmd_line = 'rm Oracle_VM_VirtualBox_Extension_Pack-4.3.20-96996.vbox-extpack'
os.system(cmd_line)

##############################################################################
# 8. install 3rd python and rsync lib
##############################################################################
cmd_line = 'wget http://%s/pip.tar' % DST_IP
os.system(cmd_line)
cmd_line = 'tar vxf pip.tar -C /tmp/'
commands.getoutput(cmd_line)
cmd_line = 'sudo pip install /tmp/*.tar.gz'
os.system(cmd_line)
cmd_line = 'sudo dpkg -i /tmp/*.deb'
os.system(cmd_line)
cmd_line = 'rm pip.tar'
commands.getoutput(cmd_line)

##############################################################################
# 9. configure rabbitmq service
##############################################################################
cmd_line = "sudo rabbitmqctl list_users | grep luhya | awk '{ print $1 }'"
ret = commands.getoutput(cmd_line)
if ret == '':
    cmd_line = 'sudo rabbitmqctl add_user luhya luhya'
    commands.getoutput(cmd_line)
    cmd_line = 'sudo rabbitmqctl set_permissions luhya  ".*" ".*" ".*" '
    commands.getoutput(cmd_line)
    cmd_line = 'sudo service rabbitmq-server restart'
    os.system(cmd_line)

##############################################################################
# 10. config django
##############################################################################
cmd_line= 'cd /usr/local/www/ && python manage.py syncdb --noinput'
os.system(cmd_line)
cmd_line = 'cd /usr/local/www/clc/sql && ./init_data.sh'
os.system(cmd_line)
cmd_line = 'mysql -uroot -proot mysql -e "select count(*) from auth_user where username=\'luhya\';" | tr -dc \'[0-9]\''
ret = commands.getoutput(cmd_line)
if ret == '0':
    cmd_line = 'cd /usr/local/www/ && python manage.py createsuperuser --username=luhya --noinput --email luhya@hoe.com --noinput'
    commands.getoutput(cmd_line)
    print '##########################################################'
    print "Please input password for default administrator(luhya)    "
    print '----------------------------------------------------------'
    cmd_line = 'python /usr/local/www/manage.py changepassword luhya'
    os.system(cmd_line)

#######################################
# 11. configure /etc/clc.conf
#######################################
with open('/storage/config/clc.conf', 'w') as myfile:
    myfile.write('[server]\n')
    myfile.write("IP=127.0.0.1\n")

cmd_line = 'sudo chown -R luhya:luhya /storage/config'
commands.getoutput(cmd_line)

##############################################################################
# 14. clear download packages
##############################################################################
cmd_line = 'sudo rm /var/cache/apt/archives/*.deb'
commands.getoutput(cmd_line)
cmd_line = 'sudo rm /var/cache/apt/archives/partial/*.deb'
commands.getoutput(cmd_line)

print '----------------------------------------------------------'
print  'Now system will reboot to enable all clc  ... ... ...'
time.sleep(1)
print '... ... ... ... ...'
cmd_line = 'sudo reboot'
commands.getoutput(cmd_line)