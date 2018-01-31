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

def checkHostIP(logger):
    logger.error("start checkHostIP ... ...")
    wmiService = wmi.WMI()
    colNicConfigs = wmiService.Win32_NetworkAdapterConfiguration(IPEnabled=True)
    for col in colNicConfigs:
        mac = col.macaddress.replace(":", "")
        #print "mac=" + mac
        mac = mac.lower()
        if mac == hostipaddr_config["mac"]:
            for ip in col.IPAddress:
                tmpip = ip.encode("utf-8")
                if tmpip == hostipaddr_config["ipaddr"][0]:
                    logger.error("HostIP configure Successfully")
                    return False
    logger.error("HostIP configure Failed, will try again !")
    return True

def setHostIP(logger):
    if hostipaddr_config["bipchange"] != "yes":
        return

    logger.error("start setHostIP ... ...")
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

def setHostName(logger):
    if hostname_config['bnamechange'] != "yes":
        return

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

    win32ui.MessageBox(u"静态IP地址设置成功，可以使用外接USB设备了！", u"桌面云系统")
    if hostname_config['breboot'] == "yes":
        os.system("shutdown /r /t 0")
