import time, os
from luhyaapi.settings import *
from luhyaapi.educloudLog import *

logger = getsshfslogger()

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

    ccip = getccipbyconf()
    base_cmd = 'sshpass -p luhya sshfs -o cache=yes,reconnect %s:/storage/space /storage/space'

    if not os.path.ismount('/storage/space'):
        logger.error("/storage/space is NOT mounted.")
        os.system("fusermount -u /storage/space")
        cmd = base_cmd % (ccip)
        logger.error("run cmd=%s" % cmd)
        os.system(cmd)
    else:
        logger.error("/storage/space is mounted.")

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
