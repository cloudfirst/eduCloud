import time, os, pexpect
from luhyaapi.settings import *
from luhyaapi.educloudLog import *

logger = getsshfslogger()

def runsshfs():
    ccip = getccipbyconf()
    base_cmd = 'sshfs -o allow_other,umask=000,cache=yes,reconnect luhya@%s:/storage/space /storage/space'

    if not os.path.ismount('/storage/space'):
        logger.error("/storage/space is NOT mounted.")
        os.system("fusermount -u /storage/space")
        cmd = base_cmd % (ccip)
        logger.error("run cmd=%s" % cmd)
        os.system(cmd)
    else:
        logger.error("/storage/space is mounted.")

def runsshfswithexpect():
    ccip = getccipbyconf()
    password = "luhya"
    base_cmd = 'sshfs -o cache=yes,reconnect luhya@%s:/storage/space /storage/space'

    if not os.path.ismount('/storage/space'):
        logger.error("/storage/space is NOT mounted.")
        os.system("fusermount -u /storage/space")
        cmd = base_cmd % (ccip)
        logger.error("run cmd=%s" % cmd)
        child = pexpect.spawn(cmd)
        i = child.expect(['password:', r"yes/no",pexpect.EOF])
        if i == 0:
            child.sendline(password)
        elif i == 1:
            child.sendline("yes")
            ret1 = child.expect(["password:",pexpect.EOF])
            if ret1 == 0:
                child.sendline(password)
        data = child.read()
        logger.error("result is %s" % data)
        child.close()
    else:
        logger.error("/storage/space is mounted.")
 

def amIcc():
    if os.path.exists('/etc/educloud/modules/cc'):
        return True
    else:
        return False

def getccipbyconf(mydebug=False):
    conf = configuration('/storage/config/cc.conf')
    ccip = conf.getvalue('server', 'IP')
    return ccip

# enhancement : http://www.tjansson.dk/2008/01/autofs-and-sshfs-the-perfect-couple/
# use both sshfs and autofs
def perform_mount():
    # mount cc's /storage/space/ to local
    if amIcc():
        logger.error("I am nc and cc, no mount any more.")
        return

    if os.path.exists('/home/luhya/.ssh/id_rsa'):
        runsshfs()
    else:
        runsshfswithexpect()

class nc_sshfs():
    def __init__(self, ):
        self._ccip = getccipbyconf(mydebug=DAEMON_DEBUG)
        logger.error("cc ip = %s" % self._ccip)

    def run(self):
        while True:
            try:
                perform_mount()
                time.sleep(5*60)
            except Exception as e:
                logger.error('nc_ssfs sexception = %s' % str(e))

def main():
    sshfser = nc_sshfs()
    sshfser.run()

if __name__ == '__main__':
    main()
