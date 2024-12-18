from django.contrib import admin
from core.models import *

admin.site.register(User)
admin.site.register(Community)
admin.site.register(Membership)
admin.site.register(Post)
admin.site.register(Comment)