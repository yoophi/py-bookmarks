from django.contrib import admin
from bookmarks.models import Link, Bookmark, Tag, SharedBookmark, Friendship

class AdminBookmark(admin.ModelAdmin):
    list_display = ("title", "link", "user", )
    list_filter = ("user", )
    ordering = ("title", )
    search_fields = ("title", )

admin.site.register(Bookmark, AdminBookmark, )
admin.site.register(Link, )
admin.site.register(Tag, )
admin.site.register(SharedBookmark, )
admin.site.register(Friendship, )
