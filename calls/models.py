from django.db import models
from accounts.models import CustomUser

class Call(models.Model):
    caller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='calls_made')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='calls_received')
    is_active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)