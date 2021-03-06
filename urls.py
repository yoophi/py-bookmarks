import os.path
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from bookmarks.feeds import *
from bookmarks.views import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

feeds = {
    'recent': RecentBookmarks,
    'user': UserBookmarks
}

urlpatterns = patterns('',
    # Example:
    # (r'^py-bookmarks/', include('py-bookmarks.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^$', main_page),
    (r'^popular/?$', popular_page),
    (r'^user/(\w+)/?$', user_page),
    (r'^login/$', 'django.contrib.auth.views.login'),
    (r'^logout/$', logout_page),
    (r'^register/$', register_page),
    (r'^register/success$', direct_to_template, { 'template': 'registration/register_success.html' }),
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': 'site_media' }),
    (r'^save/?$', bookmark_save_page),
    (r'^vote/?$', bookmark_vote_page),
    (r'^tag/([^\s]+)$', tag_page),
    (r'^tag/?$', tag_cloud_page),
    (r'^search/?$', search_page),
    (r'^bookmark/(\d+)/$', bookmark_page),
    (r'^ajax/tag/autocomplete/$', ajax_tag_autocomplete),

    # Comments
    (r'^comments/', include('django.contrib.comments.urls')),

    # Feeds
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),

    (r'^friends/(\w+)/$', friends_page),
    (r'^friend/add/(\w+)/$', friend_add),
    (r'^friend/invite/$', friend_invite),
    (r'^friend/accept/(\w+)/$', friend_accept),
)

#urlpatterns += patterns('',
#    (r'^admin/(.*)', admin.site.root),
#)
