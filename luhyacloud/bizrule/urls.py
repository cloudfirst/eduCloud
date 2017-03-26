from django.conf.urls import patterns, url
from bizrule import views

urlpatterns = patterns('',
    #url(r'^main/top/$',     views.admin_top_view,   name='main_top_view'),

    # API 1.0
    # this is a POST requtst, all data in POST section
    url(r'^postlogin$',                 views.postlogin_rule_show,          name='postlogin_rule_show'),
    url(r'^postlogin/rule/submit$',     views.postlogin_rule_submit,        name='postlogin_rule_submit'),
    url(r'^postlogin/rule/run',         views.postlogin_rule_run,           name='postlogin_rule_run'),

    url(r'^schedule$',                  views.vm_schedule_rule_show,        name='vm_schedule_rule_show'),
    url(r'^schedule/rule/submit$',      views.vm_schedule_rule_submit,      name='vm_schedule_rule_submit'),
    url(r'^schedule/rule/run',          views.vm_schedule_rule_run,         name='vm_schedule_rule_run'),

    url(r'^aim$',                       views.vm_ip_rule_show,              name='vm_ip_rule_show'),
    url(r'^aim/rule/submit$',           views.vm_ip_rule_submit,            name='vm_schedule_rule_submit'),
    url(r'^aim/rule/run',               views.vm_ip_rule_run,               name='vm_schedule_rule_run'),

)