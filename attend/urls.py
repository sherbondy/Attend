from django.conf.urls.defaults import *
import settings
from paths import static_dir

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^$', 'events.views.home'),
    (r'^logout/', 'events.views.logout_view'),
    (r'^m/(\d+)/', 'events.views.mobile'),

    # Uncomment the admin/doc line below to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

    (r'^sr/', include('socialregistration.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('django.views.static',
    (r'^static/(?P<path>.*)$', 
        'serve', {
        'document_root': static_dir,
        'show_indexes': True }),)
