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

class postloginVariables(BaseVariables):
    def __init__(self, user):
        self.login_user = user

    @string_rule_variable(label="login user name")
    def login_user_name(self):
        return self.login_user["name"]

    @string_rule_variable(label="login user group")
    def login_user_group(self):
        return self.login_user["group"]

    # Mon, Tur, Wed, Thu, Fri, Sat, Sun
    @select_rule_variable(options=['Mon', 'Tur', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    def login_time_of_day(self):
        return [time.strftime("%a")]

    # 0000-2400s
    @numeric_rule_variable(label="login_time_of_hour")
    def login_time_of_hour(self):
        ret = time.strftime("%H%M")
        return int(ret)
        #return 940

    @string_rule_variable(label="login location")
    def login_location(self):
        return self.login_user["loc"]

class postloginActions(BaseActions):
    def __init__(self, user):
        self.user = user

    @rule_action(params={'image': FIELD_TEXT})
    def set_image(self, image):
        self.user["image_list"] = [image]

    @rule_action(params={"tp": FIELD_SELECT, "pt": FIELD_SELECT})
    def test_action(self, tp, pt):
        pass

def postlogin_get_rules():
    recs = bizRule.objects.filter(rule_name="postlogin")
    if recs.count() > 0:
        rec = bizRule.objects.get(rule_name="postlogin")
        return json.loads(rec.rule_array)
    else:
        return []

def postlogin_get_variables():
    from business_rules import export_rule_data
    out = export_rule_data(postloginVariables, postloginActions)
    return json.dumps(out)

def postlogin_run(user):
    from business_rules import run_all
    rule = postlogin_get_rules()
    dv   = postloginVariables(user)
    da   = postloginActions(user)
    out = run_all(rule_list         =rule,
            defined_variables       =dv,
            defined_actions         =da,
            stop_on_first_trigger   =True
           )
    return out, user

def verify_params_in_set_image(params):
    image_name = params["image"]
    recs_1 = ecImages.objects.filter(name=image_name)
    recs_2 = ecVDS.objects.filter(name=image_name) 
    if recs_1.count() == 0 and recs_2.count() == 0:
        return False, image_name + _(" is not an valid image name")
    else:
        return True, ""

def postlogin_verify_action_params(actions):
    msg = ""
    flag = False

    for act in actions:
        if act["name"] == "set_image":
            flag, msg = verify_params_in_set_image(act["params"])
            if not flag:
                break

    return flag, msg
