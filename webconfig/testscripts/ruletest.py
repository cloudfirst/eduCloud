'''
I Post-Login Rules
1 Variables

   -
2 Actions

II Schedule Rules

III AIM Rules
'''

import time
from business_rules.variables import *
from business_rules.actions import *
from business_rules.operators import *

ex_user = {
    "name":         "thomas",
    "group":        "dongzhan",
    "image_list":   ["abc", "edf"],
    "loc":          "",
}

class postloginVariables(BaseVariables):
    def __init__(self, user):
        self.login_user = user

    @string_rule_variable(label="login user name")
    def login_user_name(self):
        return self.login_user["name"]

    @string_rule_variable(label="login user group")
    def login_user_group(self):
        return self.login_user["group"]

    @string_rule_variable(label="images list")
    def login_user_imagelist(self):
        return self.login_user["image_list"]

    # Mon, Tur, Wed, Thu, Fri, Sat, Sun
    @string_rule_variable(label="login_time_of_day")
    def login_time_of_day(self):
        return time.strftime("%a")

    # 0000-2400
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

    @rule_action(params={"myvm": FIELD_TEXT})
    def set_image(self, myvm):
        self.user["image_list"] = [myvm]

rules = [
    {
        # group name == "" and day == "" and time == ""
        "conditions":
        { "all": [
            {
                "name":     "login_user_group",
                "operator": "contains",
                "value":    "dong"
            },
            {
                "name": "login_time_of_day",
                "operator": "equal_to",
                "value": "Sat"
            },
            {
                "name": "login_time_of_hour",
                "operator": "greater_than",
                "value": 900,
            },
            {
                "name": "login_time_of_hour",
                "operator": "less_than",
                "value": 1000,
            },
        ]},
        "actions": [
            {
                "name":     "set_image",
                "params":   {"myvm": "xp"}
            }
        ],
    },
    {
        # group name == "" and day == "" and time == ""
        "conditions":
            {"all": [
                {
                    "name": "login_user_group",
                    "operator": "contains",
                    "value": "zhan"
                },
                {
                    "name": "login_time_of_day",
                    "operator": "equal_to",
                    "value": "Sat"
                },
                {
                    "name": "login_time_of_hour",
                    "operator": "greater_than",
                    "value": 1700,
                },
                {
                    "name": "login_time_of_hour",
                    "operator": "less_than",
                    "value": 1900,
                },
            ]},
        "actions": [
            {
                "name": "set_image",
                "params": {"myvm": "win7"},
            }
        ],
    },
]

#from business_rules import export_rule_data
#out = export_rule_data(postloginVariables, postloginVariables)

from business_rules import run_all


out = run_all(rule_list         =rules,
        defined_variables       =postloginVariables(ex_user),
        defined_actions         =postloginActions(ex_user),
        stop_on_first_trigger   =True
       )
print ex_user['image_list']

