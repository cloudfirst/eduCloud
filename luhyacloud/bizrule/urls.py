from django.conf.urls import patterns, url
from bizrule import views

urlpatterns = patterns('',
    #url(r'^main/top/$',     views.admin_top_view,   name='main_top_view'),

    # API 1.0
    # this is a POST requtst, all data in POST section
    url(r'^postlogin$', views.postlogin_rule_show,          name='postlogin_rule_show'),
    url(r'^schedule$',  views.vm_schedule_rule_show,        name='vm_schedule_rule_show'),
    url(r'^aim$',       views.vm_ip_rule_show,              name='vm_ip_rule_show'),

)