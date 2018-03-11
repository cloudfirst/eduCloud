# coding=UTF-8
import os
import platform as pf
import _winreg
from _winreg import ConnectRegistry, OpenKey, CloseKey, QueryInfoKey, SetValueEx
from uuid import getnode as get_mac
import wmi, json
import time, win32ui

TMP = os.environ['TMP']

hostname_config = {
    "bnamechange"   : "NAMEFLAG",
    "breboot"       : "BOOTFLAG",
    "newname"       : "new-host-name",
}

hostipaddr_config = {
    "bipchange"     : "IPFLAG",
    "ipaddr"        : ["new-host-ipaddr"],
    "ipmask"        : ["new-host-ipmask"],
    "ipgateway"     : ["new-host-ipgateway"],
    "ipdns"         : ["new-host-dns"],
    "mac"           : "new-host-mac",
}

def getActiveMAC():
    mac = get_mac()
    return ':'.join(("%012X" % mac)[i:i + 2] for i in range(0, 12, 2))

def getWindowsVersion():
    ver_str = pf.uname()
    if ver_str[2] == 'xp':
        return "WinXP"
    if ver_str[2] == '7':
        return "Win7"

def disableNetCard(logger):
    logger.error("start disableNetCard ... ...")
    try:
        wmiService = wmi.WMI()
        colNicConfigs = wmiService.Win32_NetworkAdapter()
        for col in colNicConfigs:
            if col.macaddress == None:
                logger.error("disableNetCard: ignore mac=None")
            else:
                mac = col.macaddress.replace(":", "")
                mac = mac.lower()
                if mac == hostipaddr_config["mac"]:
                    logger.error("disableNetCard: ignore mac=%s" % mac)
                else:
                    # disable it
                    logger.error("disableNetCard: disable mac=%s" % mac)
                    col.Disable()
    except Exception as e:
        logger.error("disableNetCard() get exception = %s" % str(e))

def checkHostIP(logger):
    logger.error("start checkHostIP == %s" % hostipaddr_config["ipaddr"][0])

    try:
        wmiService = wmi.WMI()
        colNicConfigs = wmiService.Win32_NetworkAdapterConfiguration(IPEnabled=True)
        for col in colNicConfigs:
            mac = col.macaddress.replace(":", "")
            logger.error("checkHostIP mac=%s" % mac)
            mac = mac.lower()
            if mac == hostipaddr_config["mac"]:
                for ip in col.IPAddress:
                    tmpip = ip.encode("utf-8")
                    logger.error("checkHostIP ip=%s" % tmpip)
                    if tmpip == hostipaddr_config["ipaddr"][0]:
                        logger.error("HostIP configure Successfully")
                        return False
        logger.error("HostIP configure Failed, will try again !")
        return True
    except Exception as e:
        logger.error("checkHostIP() get exception = %s" % str(e))
        return True

def setHostIP(logger):
    if hostipaddr_config["bipchange"] != "yes":
        return

    logger.error("start setHostIP ... ...")
    try:
        wmiService = wmi.WMI()
        colNicConfigs = wmiService.Win32_NetworkAdapterConfiguration(IPEnabled=True)
        for col in colNicConfigs:
            mac = col.macaddress.replace(":", "")
            mac = mac.lower()
            if mac == hostipaddr_config["mac"]:
                returnValue = col.EnableStatic(IPAddress=hostipaddr_config["ipaddr"],SubnetMask=hostipaddr_config["ipmask"])
                returnValue = col.SetGateways(DefaultIPGateway=hostipaddr_config["ipgateway"], GatewayCostMetric=[1])
                returnValue = col.SetDNSServerSearchOrder(DNSServerSearchOrder=hostipaddr_config["ipdns"])
        return returnValue
    except Exception as e:
        logger.error("setHostIP() get exception = %s" % str(e))

def setHostName(logger):
    if hostname_config['bnamechange'] != "yes":
        return

    try:
        aKey = OpenKey(_winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\ControlSet001\Control\ComputerName\ActiveComputerName', 0,
                       _winreg.KEY_ALL_ACCESS)
        SetValueEx(aKey, "ComputerName", 0, _winreg.REG_SZ, hostname_config['newname'])
        CloseKey(aKey)

        aKey = OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\ControlSet001\Control\ComputerName\ComputerName", 0,
                       _winreg.KEY_ALL_ACCESS)
        SetValueEx(aKey, "ComputerName", 0, _winreg.REG_SZ, hostname_config['newname'])
        CloseKey(aKey)

        aKey = OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\ControlSet001\services\Tcpip\Parameters", 0,
                       _winreg.KEY_ALL_ACCESS)
        SetValueEx(aKey, "NV Hostname", 0, _winreg.REG_SZ, hostname_config['newname'])
        CloseKey(aKey)

        aKey = OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\ControlSet001\services\Tcpip\Parameters", 0,
                       _winreg.KEY_ALL_ACCESS)
        SetValueEx(aKey, "Hostname", 0, _winreg.REG_SZ, hostname_config['newname'])
        CloseKey(aKey)
    except Exception as e:
        logger.error("setHostName() get exception = %s" % str(e))

def changeHost(logger):
    logger.error("start changeHost ... ...")
    logger.error("hostname_config = %s" % json.dumps(hostname_config))
    logger.error("hostipaddr_config = %s" % json.dumps(hostipaddr_config))

    setHostName(logger)
    flag = True
    while flag:
        time.sleep(3)
        setHostIP(logger)
        flag = checkHostIP(logger)

    disableNetCard(logger)
    win32ui.MessageBox(u"静态IP地址设置成功，可以使用外接USB设备了！", u"桌面云系统")

    if hostname_config['breboot'] == "yes":
        os.system("shutdown /r /t 0")
