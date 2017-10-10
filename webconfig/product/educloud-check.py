import os, commands, sys
import time

def prRed(prt):
    print("\033[91m {}\033[00m" .format(prt))
def prGreen(prt):
    print("\033[92m {}\033[00m" .format(prt))
def prYellow(prt):
    print("\033[93m {}\033[00m" .format(prt))
def prLightPurple(prt):
    print("\033[94m {}\033[00m" .format(prt))
def prPurple(prt):
    print("\033[95m {}\033[00m" .format(prt))
def prCyan(prt):
    print("\033[96m {}\033[00m" .format(prt))
def prLightGray(prt):
    print("\033[97m {}\033[00m" .format(prt))
def prBlack(prt):
    print("\033[98m {}\033[00m" .format(prt))

def supervisor_status():
    cmd_line = "sudo supervisorctl status"
    os.system(cmd_line)

def checkPackage( pname ):
    cmd_line = 'dpkg -l | grep %s' % pname
    output = commands.getoutput(cmd_line)
    if len(output) > 0 and output.split()[0] == 'ii':
       return True
    else:
       return False

def checkFileOwner(path, owner):
    if os.path.exists(path) == True:
        prRed("ERROR: %s NOT exist" % path)
        return

    cmd = 'stat -c "%U" %s' % path
    output = commands.getoutput(cmd)
    if output == owner:
        pass
    else:
        prRed("ERROR: owner of %s is NOT luhya" % path)

def checkLogger():
    return checkFileOwner("/var/log/educloud", "luhya")

def checkStorage():
    return checkFileOwner("/storage", "luhya")

def check_clc():
    if not checkPackage("educloud-clc"):
        prRed("ERROR: package educloud-clc NOT installed correctly.")
        return
    if not os.path.exists("/etc/educloud/modules/bizrule") == True:
        prRed("ERROR: /etc/educloud/modules/bizrule NOT exist")
        return
    if not os.path.exists("/etc/educloud/modules/core") == True:
        prRed("ERROR: /etc/educloud/modules/core NOT exist")
        return
    if not os.path.exists("/etc/educloud/modules/portal") == True:
        prRed("ERROR: /etc/educloud/modules/portal NOT exist")
        return
    if not os.path.exists("/etc/educloud/modules/virtapp") == True:
        prRed("ERROR: /etc/educloud/modules/virtapp NOT exist")
        return
    if not os.path.exists("/etc/educloud/modules/educloud.conf") == True:
        prRed("ERROR: /etc/educloud/modules/educloud.conf NOT exist")
        return

    if not checkPackage("nodedaemon-clc"):
        prRed("ERROR: package nodedaemon-clc NOT installed correctly.")
        return
    if not os.path.exists("/usr/local/nodedaemon/clc/clc_cmd_consumer") == True:
        prRed("ERROR: /usr/local/nodedaemon/clc/clc_cmd_consumer NOT exist")
        return
    if not os.path.exists("/usr/local/nodedaemon/clc/clc_status_consumer") == True:
        prRed("ERROR: /usr/local/nodedaemon/clc/clc_status_consumer NOT exist")
        return
    if not os.path.exists("/etc/supervisor/conf.d/nodedaemon-clc.conf") == True:
        prRed("ERROR: /etc/supervisor/conf.d/nodedaemon-clc.conf NOT exist")
        return
    if not os.path.exists("/storage/config/clc.conf") == True:
        prRed("ERROR: /storage/config/clc.conf NOT exist")
        return

    if not checkPackage("mysql-server"):
        prRed("ERROR: package mysql-server NOT installed correctly.")
        return

    if not checkPackage("rabbitmq-server"):
        prRed("ERROR: package mysql-server NOT installed correctly.")
        return

    #####
    prGreen("checking clc ... ...              OK")

def check_walrus():
    prGreen("checking walrus ... ...           OK")

def check_cc():
    if not checkPackage("educloud-cc"):
        prRed("ERROR: package educloud-cc NOT installed correctly.")
        return
    if not checkPackage("nodedaemon-cc"):
        prRed("ERROR: package nodedaemon-cc NOT installed correctly.")
        return
    if not os.path.exists("/etc/supervisor/conf.d/nodedaemon-cc.conf") == True:
        prRed("ERROR: /etc/supervisor/conf.d/nodedaemon-cc.conf NOT exist")
        return
    if not os.path.exists("/usr/local/nodedaemon/cc/cc_status_consumer") == True:
        prRed("ERROR: /usr/local/nodedaemon/cc/cc_status_consumer NOT exist")
        return
    if not os.path.exists("/usr/local/nodedaemon/cc/cc_cmd_consumer") == True:
        prRed("ERROR: /usr/local/nodedaemon/cc/cc_cmd_consumer NOT exist")
        return
    if not os.path.exists("/usr/local/nodedaemon/cc/cc_rpc_server") == True:
        prRed("ERROR: /usr/local/nodedaemon/cc/cc_rpc_server NOT exist")
        return
    if not os.path.exists("/usr/local/nodedaemon/cc/cc_status_publisher") == True:
        prRed("ERROR: /usr/local/nodedaemon/cc/cc_status_publisher NOT exist")
        return
    if not os.path.exists("/storage/config/clc.conf") == True:
        prRed("ERROR: /storage/config/clc.conf NOT exist")
        return
    if not checkPackage("rabbitmq-server"):
        prRed("ERROR: package mysql-server NOT installed correctly.")
        return

    prGreen("checking cc ... ...               OK")

def check_nc():
    if not checkPackage("nodedaemon-cc"):
        prRed("ERROR: package nodedaemon-cc NOT installed correctly.")
        return
    if not os.path.exists("/etc/supervisor/conf.d/nodedaemon-nc.conf") == True:
        prRed("ERROR: /etc/supervisor/conf.d/nodedaemon-nc.conf NOT exist")
        return
    if not os.path.exists("/usr/local/nodedaemon/nc/nc_cmd_consumer") == True:
        prRed("ERROR: /usr/local/nodedaemon/nc/nc_cmd_consumer NOT exist")
        return
    if not os.path.exists("/usr/local/nodedaemon/nc/nc_status_publisher") == True:
        prRed("ERROR: /usr/local/nodedaemon/nc/nc_status_publisher NOT exist")
        return
    if not os.path.exists("/storage/config/cc.conf") == True:
        prRed("ERROR: /storage/config/cc.conf NOT exist")
        return

    prGreen("checking nc ... ...               OK")


def main(argv):
    flag = 0
    if os.path.exists("/etc/educloud/modules/clc") == True:
        flag += 1
        check_clc()

    if os.path.exists("/etc/educloud/modules/walrus") == True:
        flag += 1
        check_walrus()

    if os.path.exists("/etc/educloud/modules/cc") == True:
        flag += 1
        check_cc()

    if os.path.exists("/etc/educloud/modules/nc") == True:
        flag += 1
        check_nc()

    if flag > 0:
        supervisor_status()

if __name__ == "__main__":
   main(sys.argv[1:])