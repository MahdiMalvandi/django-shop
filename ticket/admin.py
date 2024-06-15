from django.contrib import admin
from .models import *


class MessageInline(admin.TabularInline):
    model = Message


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'creator', 'created']
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'content']
