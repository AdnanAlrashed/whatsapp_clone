from django.db import models
from accounts.models import CustomUser

class Call(models.Model):
    CALL_TYPES = [
        ('audio', 'مكالمة صوتية'),
        ('video', 'مكالمة فيديو'),
    ]
    
    CALL_STATUS = [
        ('initiated', 'تم البدء'),
        ('ongoing', 'جارية'),
        ('completed', 'مكتملة'),
        ('missed', 'فائتة'),
        ('rejected', 'مرفوضة'),
    ]
    
    caller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='calls_made')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='calls_received')
    call_type = models.CharField(max_length=10, choices=CALL_TYPES, default='audio')
    status = models.CharField(max_length=10, choices=CALL_STATUS, default='initiated')
    is_active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)  # استخدام timestamp بدلاً من started_at
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'مكالمة'
        verbose_name_plural = 'المكالمات'

    def __str__(self):
        return f"{self.get_call_type_display()} من {self.caller.email} إلى {self.receiver.email}"

    def save(self, *args, **kwargs):
        if self.ended_at and self.timestamp:
            self.duration = self.ended_at - self.timestamp
        super().save(*args, **kwargs)