from django.contrib import admin
from .models import Post, Profile

class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'date_posted')
    search_fields = ('title', 'content')
    list_filter = ('date_posted', 'author')
    readonly_fields = ('date_posted',)
admin.site.register(Post, PostAdmin)
admin.site.register(Profile)
