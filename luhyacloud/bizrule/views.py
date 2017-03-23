from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from clc.models import *

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

@login_required(login_url='/portal/admlogin')
def postlogin_rule_show(request):
    u = User.objects.get(username=request.user)
    ua = ecAccount.objects.get(userid=request.user)

    context = {
        'uid':   u.username,
        'showname': ua.showname,
        'dashboard' : _("PostLogin Rules"),
        'variables' : postlogin_get_variables(),
        'rules' :  postlogin_get_rules(),
        'images':  get_all_images(),
    }

    return render(request, 'bizrule/test.html', context)

@login_required(login_url='/portal/admlogin')
def vm_schedule_rule_show(request):
    pass

@login_required(login_url='/portal/admlogin')
def vm_ip_rule_show(request):
    pass