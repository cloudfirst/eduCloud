from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from clc.models import *
from models import *

import json
import random, pickle, pexpect, os, base64, shutil, time, datetime
import logging
import commands
from datetime import datetime

from luhyaapi.educloudLog import *
from luhyaapi.hostTools import *
import time
from business_rules.variables import *
from business_rules.actions import *
from business_rules.operators import *
from postlogin_rule import *
from vmschedule_rule import *
from aim_rule import *

logger = getclclogger()

from prometheus_client import CollectorRegistry, Gauge, write_to_textfile, Counter
registry = CollectorRegistry()

metrics_dst_dir    = "/storage/config/metrics/"
metrics_dst_file   = "bizrule-views.prom"

num_rules = Gauge('num_of_rules', 'number of rules', ['type'], registry=registry)

def _init_prometheus_metrics():
    num_rules.labels(type="postlogin").set(0)
    num_rules.labels(type="schedule").set(0)
    num_rules.labels(type="aim").set(0)

    from prometheus_client.parser import text_string_to_metric_families
    if not os.path.exists(metrics_dst_dir + metrics_dst_file):
        write_to_textfile(metrics_dst_dir + metrics_dst_file, registry)
    else:
        text = open(metrics_dst_dir + metrics_dst_file, 'r').read()
        for family in text_string_to_metric_families(text):
            for sample in family.samples:
                metric_name   = sample[0]
                metric_labels = sample[1]
                metric_value  = sample[2]
                if metric_name == "num_of_rules":
                    logger.error("prometheus: retrieve metric num_of_rules with value %d" % metric_value)
                    num_rules.labels(type = metric_labels["type"]).set(metric_value)

_init_prometheus_metrics()

def get_all_images():
    image_list = []
    recs = ecImages.objects.all()
    for rec in recs:
        image_list.append(rec.name)

    return json.dumps(image_list)

###############################################
# POST LOGIN RULE handles
##############################################
@login_required(login_url='/portal/admlogin')
def postlogin_rule_show(request):
    u = User.objects.get(username=request.user)
    ua = ecAccount.objects.get(userid=request.user)

    context = {
        'uid':   u.username,
        'showname': ua.showname,
        'dashboard' : _("PostLogin Rules"),
        'variables' : postlogin_get_variables(),
        'rules' :  json.dumps(postlogin_get_rules()),
    }

    return render(request, 'bizrule/postlogin.html', context)

def postlogin_rule_submit(request):
    flag = True
    msg = ""
    rule_type  = request.POST['rule_type']
    rule_array = request.POST['rule_array']

    # verify action params
    rules = json.loads(rule_array)
    num_rules.labels(type="postlogin").set(0)
    for rule in rules:
        num_rules.labels(type="postlogin").inc()
        actions = rule["actions"]
        flag, msg = postlogin_verify_action_params(actions)
        if not flag:
            break
    write_to_textfile(metrics_dst_dir + metrics_dst_file, registry)

    response = {}
    if flag:
        recs = bizRule.objects.filter(rule_name=rule_type)
        if recs.count() > 0: # update exist record
            rec = bizRule.objects.get(rule_name=rule_type)
            rec.rule_array = rule_array
            rec.save()
        else:  # add new record
            rec = bizRule(
                rule_name=rule_type,
                rule_array=rule_array,
            )
            rec.save()
        response['Result'] = 'OK'
    else:
        response['Result'] = 'FAIL'
        response['errormsg'] = msg

    retvalue = json.dumps(response)
    return HttpResponse(retvalue, content_type="application/json")

def postlogin_rule_run(request):
    response = {}
    try:
        rule = bizRule.objects.get(rule_name="postlogin")
        if len(rule.rule_array) > 0:
            user = {}
            user["name"] = request.POST["name"]
            user["loc"] = request.POST["loc"]
            user["group"] = request.POST["group"]
            user["image_list"] = json.loads(request.POST["image_list"])
            triggered, result = postlogin_run(user)
            response['Result'] = 'OK'
            response["triggered"] = triggered
            response["data"] = result
    except Exception as e:
        logger.error("postlogin db read get exception.")
        response['Result'] = 'FAIL'
        response['reason'] = str(e)

    retvalue = json.dumps(response)
    return HttpResponse(retvalue, content_type="application/json")


###############################################
# VM SCHEDULE RULE handles
##############################################
@login_required(login_url='/portal/admlogin')
def vm_schedule_rule_show(request):
    u = User.objects.get(username=request.user)
    ua = ecAccount.objects.get(userid=request.user)

    context = {
        'uid':   u.username,
        'showname': ua.showname,
        'dashboard' : _("VM Schedule Rules"),
        'variables' : vmSchedule_get_variables(),
        'rules' :  json.dumps(vmSchedule_get_rules()),
    }

    return render(request, 'bizrule/vmschedule.html', context)

def vm_schedule_rule_submit(request):
    flag = True
    msg = ""
    rule_type  = request.POST['rule_type']
    rule_array = request.POST['rule_array']

    # verify action params
    rules = json.loads(rule_array)
    num_rules.labels(type="schedule").set(0)
    for rule in rules:
        num_rules.labels(type="schedule").inc()
        actions = rule["actions"]
        flag, msg = vmschedule_verify_action_params(actions)
        if not flag:
            break
    write_to_textfile(metrics_dst_dir + metrics_dst_file, registry)

    response = {}
    if flag:
        recs = bizRule.objects.filter(rule_name=rule_type)
        if recs.count() > 0: # update exist record
            rec = bizRule.objects.get(rule_name=rule_type)
            rec.rule_array = rule_array
            rec.save()
        else:  # add new record
            rec = bizRule(
                rule_name=rule_type,
                rule_array=rule_array,
            )
            rec.save()
        response['Result'] = 'OK'
    else:
        response['Result'] = 'FAIL'
        response['errormsg'] = msg

    retvalue = json.dumps(response)
    return HttpResponse(retvalue, content_type="application/json")


def vm_schedule_rule_run(request):
    response = {}
    try:
        rule = bizRule.objects.get(rule_name="vmschedule")
        if len(rule.rule_array) > 0:
            vm = json.loads(request.POST["vm"])
            user = json.loads(request.POST["user"])
            triggered, result = vmSchedule_run(user, vm)
            response['Result'] = 'OK'
            response["triggered"] = triggered
            response["data"] = result
    except Exception as e:
        response['Result'] = 'FAIL'
        response['reason'] = str(e)

    retvalue = json.dumps(response)
    return HttpResponse(retvalue, content_type="application/json")

###############################################
# IP-MAC TABLE RULE handles
##############################################
@login_required(login_url='/portal/admlogin')
def vm_ip_rule_show(request):
    u = User.objects.get(username=request.user)
    ua = ecAccount.objects.get(userid=request.user)

    context = {
        'uid':   u.username,
        'showname': ua.showname,
        'dashboard' : _("Account/IP/MAC Rules"),
        'variables' : aim_get_variables(),
        'rules' :  json.dumps(aim_get_rules()),
    }

    return render(request, 'bizrule/aim.html', context)

def vm_ip_rule_submit(request):
    flag = True
    msg = ""
    rule_type  = request.POST['rule_type']
    rule_array = request.POST['rule_array']

    # verify action params
    rules = json.loads(rule_array)
    num_rules.labels(type="aim").set(0)
    for rule in rules:
        num_rules.labels(type="aim").inc()
        actions = rule["actions"]
        flag, msg = aim_verify_action_params(actions)
        if not flag:
            break
    write_to_textfile(metrics_dst_dir + metrics_dst_file, registry)

    response = {}
    if flag:
        recs = bizRule.objects.filter(rule_name=rule_type)
        if recs.count() > 0: # update exist record
            rec = bizRule.objects.get(rule_name=rule_type)
            rec.rule_array = rule_array
            rec.save()
        else:  # add new record
            rec = bizRule(
                rule_name=rule_type,
                rule_array=rule_array,
            )
            rec.save()
        response['Result'] = 'OK'
    else:
        response['Result'] = 'FAIL'
        response['errormsg'] = msg

    retvalue = json.dumps(response)
    return HttpResponse(retvalue, content_type="application/json")

def vm_ip_rule_run(request):
    response = {}
    try:
        rule = bizRule.objects.get(rule_name="aim")
        if len(rule.rule_array) > 0:
            vm = json.loads(request.POST["vm"])
            user = json.loads(request.POST["user"])
            triggered, result = aim_run(user, vm)
            response['Result'] = 'OK'
            response["triggered"] = triggered
            response["data"] = result
    except Exception as e:
        response['Result'] = 'FAIL'
        response['reason'] = str(e)

    retvalue = json.dumps(response)
    return HttpResponse(retvalue, content_type="application/json")
