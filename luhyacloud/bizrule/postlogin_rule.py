# coding=UTF-8
import time, json
from business_rules.variables import *
from business_rules.actions import *
from business_rules.operators import *
from models import *

ex_user = {
    "name":         "thomas",
    "group":        "dongzhan",
    "image_list":   ["abc", "edf"],
    "loc":          "",
}

def export_user_images():
    result = []
    for image in ex_user['image_list']:
        op = {}
        op['label'] = image
        op['name']  = image
        result.append(op)
    return result

class postloginVariables(BaseVariables):
    def __init__(self, user):
        self.login_user = user

    @string_rule_variable(label="login user name")
    def login_user_name(self):
        return self.login_user["name"]

    @string_rule_variable(label="login user group")
    def login_user_group(self):
        return self.login_user["group"]

    @select_rule_variable(options=ex_user['image_list'])
    def login_user_image(self):
        return self.login_user["image_list"][0]

    # Mon, Tur, Wed, Thu, Fri, Sat, Sun
    @select_rule_variable(options=['Mon', 'Tur', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    def login_time_of_day(self):
        return time.strftime("%a")

    # 0000-2400s
    @numeric_rule_variable(label="login_time_of_hour")
    def login_time_of_hour(self):
        #return int(time.strftime("%H%M"))
        return 940

    @string_rule_variable(label="login location")
    def login_location(self):
        return self.login_user["loc"]

class postloginActions(BaseActions):
    def __init__(self, user):
        self.user = user

    @rule_action(params={'image': FIELD_SELECT})
    def set_image(self, image):
        self.user["image_list"] = [image]

    @rule_action(params={"tp": FIELD_SELECT, "pt": FIELD_SELECT})
    def test_action(self, tp, pt):
        pass
#
# def postlogin_get_rules():
#     rules = [
#         {
#             # group name == "" and day == "" and time == ""
#             "conditions":
#             { "all":
#                 [
#                     {
#                         "name": "login_time_of_day",
#                         "operator": "equal_to",
#                         "value": "Sat"
#                     },
#                     {
#                         "name": "login_time_of_hour",
#                         "operator": "greater_than",
#                         "value": 900,
#                     },
#                     {
#                         "name": "login_time_of_hour",
#                         "operator": "less_than",
#                         "value": 1000,
#                     },
#                     {"any": [
#                         {
#                             "name": "login_user_group",
#                             "operator": "contains",
#                             "value": "dong"
#                         },
#                         {
#                             "name": "login_time_of_hour",
#                             "operator": "less_than",
#                             "value": 1000,
#                         },
#                     ]},
#                 ]
#             },
#             "actions":
#                 [
#                     {
#                         "name":     "set_image",
#                         "params":   {"image": "xp"}
#                     }
#                 ],
#         },
#         {
#             # group name == "" and day == "" and time == ""
#             "conditions":
#                 {"all": [
#                     {
#                         "name": "login_user_group",
#                         "operator": "contains",
#                         "value": "zhan"
#                     },
#                     {
#                         "name": "login_time_of_day",
#                         "operator": "equal_to",
#                         "value": "Sat"
#                     },
#                     {
#                         "name": "login_time_of_hour",
#                         "operator": "greater_than",
#                         "value": 1700,
#                     },
#                     {
#                         "name": "login_time_of_hour",
#                         "operator": "less_than",
#                         "value": 1900,
#                     },
#                 ]},
#             "actions": [
#                 {
#                     "name": "set_image",
#                     "params": {"image": "win7"},
#                 }
#             ],
#         },
#     ]
#     return json.dumps(rules)

def postlogin_get_rules():
    recs = bizRule.objects.filter(rule_name="postlogin")
    if recs.count() > 0:
        rec = bizRule.objects.get(rule_name="postlogin")
        return json.dumps(rec.rule_array)
    else:
        return []

def postlogin_get_variables():
    from business_rules import export_rule_data
    out = export_rule_data(postloginVariables, postloginActions)
    return json.dumps(out)

def postlogin_run():
    from business_rules import run_all
    out = run_all(rule_list         =rules,
            defined_variables       =postloginVariables(ex_user),
            defined_actions         =postloginActions(ex_user),
            stop_on_first_trigger   =True
           )
    print ex_user['image_list']

