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

logger = getclclogger()

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
        'images':  get_all_images(),
    }

    return render(request, 'bizrule/test.html', context)


def postlogin_rule_submit(request):
    rule_type  = request.POST['rule_type']
    rule_array = request.POST['rule_array']
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

    response = {}
    response['Result'] = 'OK'
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
        response['Result'] = 'FAIL'
        response['reason'] = str(e)

    retvalue = json.dumps(response)
    return HttpResponse(retvalue, content_type="application/json")


###############################################
# VM SCHEDULE RULE handles
##############################################
@login_required(login_url='/portal/admlogin')
def vm_schedule_rule_show(request):
    pass

def vm_schedule_rule_submit(request):
    pass

def vm_schedule_rule_run(requet):
    pass

###############################################
# IP-MAC TABLE RULE handles
##############################################
@login_required(login_url='/portal/admlogin')
def vm_ip_rule_show(request):
    pass

def vm_ip_rule_submit(request):
    pass

def vm_ip_rule_run(request):
    pass


