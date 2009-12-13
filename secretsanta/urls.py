from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('djangosanta.secretsanta.views',
	url(r'^about/$', 'direct_to_template', {'template':'about.html'}, name="about"),
	url(r'^privacy/$', 'direct_to_template', {'template':'privacy.html'}, name="privacy"),	
	url(r'^support/$', 'direct_to_template', {'template':'support.html'}, name="support"),
	url(r'^request/$', 'request_invite', name="request-invite"),
	url(r'^invitefriends/(?P<group_id>\d+)/$', 'invite_friends', name="invite-friends"),	
	url(r'^confirmrequest/$', 'confirm_request', name='confirm_request'),
	url(r'^resend/$', 'resend_invite', name="resend-invite"),	
	url(r'^interests/$', 'add_interests', name="interests"),		
	url(r'^register/$', 'register', name="register"),	
	url(r'^deletemember/(?P<group_id>\d+)/(?P<member_name>.+)/$', 'delete_member', name="delete-member"),			
	url(r'^members/(?P<group_id>\d+)/$', 'edit_members', name="edit-members"),		
	url(r'^create/$', 'group', name="create"),
	url(r'^deletegroup/(?P<group_id>.+)/$', 'delete_group', name="delete-group"),	
	url(r'^joingroup/$', 'join_group', name="join-group"),	
	url(r'^editgroup/(?P<group_id>\d+)/$', 'group', name="editgroup"),	
	url(r'^login/$', 'login', name="login"),
	url(r'^actions/$', 'actions', name="actions"),
	url(r'^suggestions/(?P<keyword>[^/]+)/$', 'gift_suggestions', name="gift-suggestions"),
	url(r'^$', 'home', name="home"),
)

urlpatterns += patterns('',
	url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name="logout"),	
)
