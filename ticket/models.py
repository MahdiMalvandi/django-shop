from django.db import models
from user.models import User


class OpenChats(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_open=True)


class Chat(models.Model):
    title = models.CharField(max_length=200)
    is_open = models.BooleanField(default=True)
    creator = models.ForeignKey(User, related_name='chats', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    opens = OpenChats()
    objects = models.Manager()


class Message(models.Model):
    user = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    content = models.TextField(max_length=500)
    created = models.DateTimeField(auto_now_add=True)
