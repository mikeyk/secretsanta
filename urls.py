from django.conf.urls.defaults import *
from django.conf import settings

from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',

    (r'^', include('djangosanta.secretsanta.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/Users/mkrieger/Dropbox/Secret Santa/djangosanta/media'}),
    )