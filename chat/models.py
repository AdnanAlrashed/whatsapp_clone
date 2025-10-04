from django.db import models
from accounts.models import CustomUser
from django.utils import timezone

class ChatRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)  # استخدام default بدلاً من auto_now_add
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.email}: {self.content[:20]}"