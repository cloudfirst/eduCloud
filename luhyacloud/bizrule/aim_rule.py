# coding=UTF-8
import time, json
from business_rules.variables import *
from business_rules.actions import *
from business_rules.operators import *
from models import *
from clc.models import *
from django.utils.translation import ugettext as _
from luhyaapi.hostTools import *

from luhyaapi.educloudLog import *
logger = getclclogger()

class aimVariables(BaseVariables):
    def __init__(self, user, vm):
        self.user = user
        self.vm   = vm

    @string_rule_variable(label="user name")
    def user_name(self):
        return self.user["user_name"]

    @string_rule_variable(label="user id")
    def user_id(self):
        return self.user["user_id"]

    @string_rule_variable(label="user group")
    def user_group(self):
        return self.user["user_group"]

    @string_rule_variable(label="vm ccname")
    def vm_ccname(self):
        return self.vm["ccname"]

    @string_rule_variable(label="vm ccip")
    def vm_ccip(self):
        return self.vm["ccip"]

    @string_rule_variable(label="vm ncip")
    def vm_ncip(self):
        return self.vm["ncip"]

    @string_rule_variable(label="vm name")
    def vm_name(self):
        return self.vm["name"]

class aimActions(BaseActions):
    def __init__(self, user, vm):
        self.user = user
        self.vm   = vm

    @rule_action(params={'ip':      FIELD_TEXT,
                         "mask":    FIELD_TEXT,
                         "gateway": FIELD_TEXT,
                         "dns":     FIELD_TEXT,
                         "reboot":  FIELD_TEXT})
    def set_ip(self, ip, mask, gateway, dns, reboot):
        self.vm["ip"]       = ip
        self.vm["mask"]     = mask
        self.vm["gateway"]  = gateway
        self.vm["dns"]      = dns
        self.vm["mac"]      = randomMAC()
        self.vm["reboot"]   = reboot.lower()
        logger.error("set_ip reboot = %s" % self.vm["reboot"])

    @rule_action(params={'ip': FIELD_TEXT,
                         "mask": FIELD_TEXT,
                         "gateway": FIELD_TEXT,
                         "dns": FIELD_TEXT,
                         "mac": FIELD_TEXT,
                         "reboot": FIELD_TEXT})
    def set_ip_mac(self, ip, mask, gateway, dns, mac, reboot):
        self.vm["ip"]       = ip
        self.vm["mask"]     = mask
        self.vm["gateway"]  = gateway
        self.vm["dns"]      = dns
        self.vm["reboot"]   = reboot.lower()
        logger.error("set_ip_mac reboot = %s" % self.vm["reboot"])
        if mac == "any":
            self.vm["mac"]  = randomMAC()
        else:
            self.vm['mac']  = mac

    @rule_action(params={
        "prefix": FIELD_TEXT,
        "mask": FIELD_TEXT,
        "gateway": FIELD_TEXT,
        "dns":      FIELD_TEXT,
        "express":  FIELD_TEXT,
        "reboot" : FIELD_TEXT
    })
    def set_calc_ip(self, prefix, mask, gateway, dns, express, reboot):
        import re
        acc_no = re.findall("\d+", self.user["user_id"])[0]
        acc_no = int(acc_no)
        acc_no = eval(express)(acc_no)
        self.vm["ip"]       = prefix + "." + str(acc_no)
        self.vm["mask"]     = mask
        self.vm["gateway"]  = gateway
        self.vm["dns"]      = dns
        self.vm["mac"]      = randomMAC()
        self.vm["reboot"]   = reboot.lower()
        logger.error("set_calc_ip reboot = %s" % self.vm["reboot"])

def aim_get_rules():
    recs = bizRule.objects.filter(rule_name="aim")
    if recs.count() > 0:
        rec = bizRule.objects.get(rule_name="aim")
        return json.loads(rec.rule_array)
    else:
        return []

def aim_get_variables():
    from business_rules import export_rule_data
    out = export_rule_data(aimVariables, aimActions)
    return json.dumps(out)

def aim_run(user, vm):

    from business_rules import run_all
    rule = aim_get_rules()
    dv   = aimVariables(user, vm)
    da   = aimActions(user, vm)
    out = run_all(rule_list         =rule,
            defined_variables       =dv,
            defined_actions         =da,
            stop_on_first_trigger   =True
           )
    return out, vm

def verify_params_in_set_ipmac(params):
    flag = True
    msg  = ""
    keys = params.keys()
    for key in keys:
        if key == "ip":
            if len(params[key].split(".")) == 4:
                pass
            else:
                return False, params[key] + _(" is not a valid ip address")
        elif key == "mask":
            if len(params[key].split(".")) == 4:
                pass
            else:
                return False, params[key] + _(" is not a valid network mask")
        elif key == "gateway":
            if len(params[key].split(".")) == 4:
                pass
            else:
                return False, params[key] + _(" is not a valid gateway address")
        elif key == "mac":
            if params[key] == "any" or len(params[key]) == 12:
                pass
            else:
                return False, params[key] + _(" is not a valid mac address, sample is 0800275eb57d")
        elif key == "prefix":
            if len(params[key].split(".")) == 3:
                pass
            else:
                return False, params[key] + _(" is not a valid network preifx, sample is 192.168.1")
        elif key == "dns":
            if len(params[key].split(".")) == 4:
                pass
            else:
                return False, params[key] + _(" is not a valid dns address")
        elif key=="express":
            if params[key].find("lambda") == 0:
                pass
            else:
                return False, params[key] + _(" is not a valid lambda expression")
        elif key=="reboot":
            reboot = params[key]
            if reboot.lower() == "yes" or reboot.lower() == "no":
                pass
            else:
                return False, params[key] + _(" is not a reboot value, sample either yes or no")

    return flag, msg

def aim_verify_action_params(actions):
    msg = ""
    flag = False

    for act in actions:
            flag, msg = verify_params_in_set_ipmac(act["params"])
            if not flag:
                break

    return flag, msg