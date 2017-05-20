# coding=UTF-8
import time, json
from business_rules.variables import *
from business_rules.actions import *
from business_rules.operators import *
from models import *
from clc.models import *
from django.utils.translation import ugettext as _

from luhyaapi.educloudLog import *
logger = getclclogger()

class vmScheduleVariables(BaseVariables):
    def __init__(self, user, vm):
        self.vm = vm
        self.user = user

    @string_rule_variable(label="user id")
    def user_id(self):
        return self.user["user_id"]

    @string_rule_variable(label="user name")
    def user_name(self):
        return self.user["user_name"]

    @string_rule_variable(label="user group")
    def user_group(self):
        return self.user["user_group"]

    @boolean_rule_variable(label="user usb")
    def user_usb(self):
        return self.user["user_usb"]

    # @boolean_rule_variable(label="user superuser")
    # def user_superuser(self):
    #     return self.user["user_superuser"]

    # @boolean_rule_variable(label="user email")
    # def user_email(self):
    #     return self.user["user_email"]

    @string_rule_variable(label="vm name")
    def vm_name(self):
        return self.vm["name"]

    @string_rule_variable(label="vm src imageid")
    def vm_src_imageid(self):
        return self.vm["src_imageid"]

    @string_rule_variable(label="vm dst imageid")
    def vm_dst_imageid(self):
        return self.vm["dst_imageid"]

    @string_rule_variable(label="vm insid")
    def vm_insid(self):
        return self.vm["insid"]

    @numeric_rule_variable(label="vm memory")
    def vm_memory(self):
        return self.vm["memory"]

    @numeric_rule_variable(label="vm cpus")
    def vm_cpus(self):
        return self.vm["cpus"]

    @select_rule_variable(options=['desktop', 'server'])
    def vm_usage(self):
        return [self.vm["usage"]]

    @select_rule_variable(options=['WindowsXP', 'Windows7', 'Ubuntu_64', 'Windows8', 'Windows2003', 'Windows2003_64', 'Windows2008', 'Windows2008_64', 'Windows2012_64'])
    def vm_ostype(self):
        return [self.vm["ostype"]]

    @select_rule_variable(options=['vbox', 'kvm'])
    def vm_hypervisor(self):
        return [self.vm["hypervisor"]]


class vmScheduleActions(BaseActions):
    def __init__(self, vm):
        self.vm = vm

    @rule_action(params={'cc': FIELD_TEXT,
                         "nc": FIELD_TEXT})
    def set_destination(self, cc, nc):
        self.vm["cc"] = cc
        self.vm['nc'] = nc

def vmSchedule_get_rules():
    recs = bizRule.objects.filter(rule_name="vmschedule")
    if recs.count() > 0:
        rec = bizRule.objects.get(rule_name="vmschedule")
        return json.loads(rec.rule_array)
    else:
        return []

def vmSchedule_get_variables():
    from business_rules import export_rule_data
    out = export_rule_data(vmScheduleVariables, vmScheduleActions)
    return json.dumps(out)

def vmSchedule_run(user, vm):
    from business_rules import run_all
    rule = vmSchedule_get_rules()
    dv   = vmScheduleVariables(user, vm)
    da   = vmScheduleActions(vm)
    out = run_all(rule_list         =rule,
            defined_variables       =dv,
            defined_actions         =da,
            stop_on_first_trigger   =True
           )
    return out, vm


def verify_params_in_set_dst(params):
    cc_def = params["cc"]
    nc_def = params["nc"]

    ccs = ecServers.objects.filter(role="cc", ccname=cc_def)
    if ccs.count() > 0:
        if nc_def == "any":
            return True, ""
        else:
            ncs = ecServers.objects.filter(role="nc", ip0=nc_def, ccname=cc_def)
            if ncs.count() > 0:
                return True, ""
            else:
                return False, nc_def + _(" is not an valid nc ip")
    else:
        return False, cc_def + _(" is not an valid cluster name")

def vmschedule_verify_action_params(actions):
    msg = ""
    flag = False

    for act in actions:
        if act["name"] == "set_destination":
            flag, msg = verify_params_in_set_dst(act["params"])
            if not flag:
                break

    return flag, msg