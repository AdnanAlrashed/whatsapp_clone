from django.db import models
from accounts.models import CustomUser
from django.utils import timezone
import uuid

class ChatRoom(models.Model):
    ROOM_TYPES = [
        ('public', 'عامة'),
        ('private', 'خاصة'),
        ('group', 'مجموعة'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='public')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    max_participants = models.IntegerField(default=50)
    
    # للمجموعات الخاصة
    participants = models.ManyToManyField(CustomUser, related_name='chat_rooms', blank=True)
    admins = models.ManyToManyField(CustomUser, related_name='admin_rooms', blank=True)
    online_users = models.ManyToManyField(
        CustomUser, 
        through='OnlineUser',
        related_name='online_rooms',
        blank=True
    )
    
    class Meta:
        unique_together = ['name', 'room_type']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"
    
    def get_online_count(self):
        """الحصول على عدد المستخدمين المتصلين في الغرفة"""
        try:
            # استخدام OnlineUser model للعد
            return self.online_users.filter(
                onlineuser__is_online=True
            ).distinct().count()
        except Exception as e:
            print(f"Error in get_online_count: {e}")
            return 0
        
    def add_online_user(self, user):
        """إضافة مستخدم إلى قائمة المتصلين"""
        try:
            online_user, created = OnlineUser.objects.get_or_create(
                user=user,
                room=self,
                defaults={'is_online': True}
            )
            if not created:
                online_user.is_online = True
                online_user.last_seen = timezone.now()
                online_user.save()
            return True
        except Exception as e:
            print(f"Error adding online user: {e}")
            return False
    
    def remove_online_user(self, user):
        """إزالة مستخدم من قائمة المتصلين"""
        try:
            OnlineUser.objects.filter(
                user=user,
                room=self
            ).update(is_online=False, last_seen=timezone.now())
            return True
        except Exception as e:
            print(f"Error removing online user: {e}")
            return False
    
    def can_join(self, user):
        if self.room_type == 'public':
            return True
        elif self.room_type == 'private':
            return self.participants.filter(id=user.id).exists()
        return False

class RoomInvitation(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='invitations')
    invited_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_invitations')
    invited_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_invitations')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_accepted = models.BooleanField(default=False)
    is_declined = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        unique_together = ['room', 'invited_user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"دعوة {self.invited_user.email} إلى {self.room.name}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_active(self):
        return not self.is_accepted and not self.is_declined and not self.is_expired()

    
    def get_status_display(self):
        """الحصول على حالة الدعوة كنص"""
        if self.is_accepted:
            return "مقبولة"
        elif self.is_declined:
            return "مرفوضة"
        elif self.is_expired():
            return "منتهية"
        else:
            return "قيد الانتظار"

class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'نص'),
        ('image', 'صورة'),
        ('file', 'ملف'),
        ('system', 'نظام'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(blank=True, null=True)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True)
    
    # لحذف الرسائل بشكل انتقائي
    deleted_for = models.ManyToManyField(CustomUser, related_name='deleted_messages', blank=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['room', 'timestamp']),
            models.Index(fields=['sender', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.sender.email}: {self.content[:20]}"
    
    def is_deleted_for_user(self, user):
        return self.deleted_for.filter(id=user.id).exists()

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='chat_profile')
    display_name = models.CharField(max_length=50, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    status = models.CharField(max_length=20, default='online', choices=[
        ('online', 'متصل'),
        ('away', 'بعيد'),
        ('busy', 'مشغول'),
        ('offline', 'غير متصل'),
    ])
    last_seen = models.DateTimeField(auto_now=True)
    theme = models.CharField(max_length=20, default='light', choices=[
        ('light', 'فاتح'),
        ('dark', 'داكن'),
        ('auto', 'تلقائي'),
    ])
    
    def __str__(self):
        return f"{self.user.email} Profile"

# في chat/models.py - تأكد من نموذج OnlineUser
class OnlineUser(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'room']
        verbose_name = 'مستخدم متصل'
        verbose_name_plural = 'المستخدمون المتصلون'
    
    def __str__(self):
        return f"{self.user.email} - {self.room.name} ({'online' if self.is_online else 'offline'})"

# في نهاية chat/models.py أضف هذه الإشارة
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """إنشاء UserProfile تلقائياً عند إنشاء مستخدم جديد"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """حفظ UserProfile عند حفظ المستخدم"""
    if hasattr(instance, 'chat_profile'):
        instance.chat_profile.save()


    
    
    
    
    

@receiver(post_save, sender=RoomInvitation)
def send_invitation_notification(sender, instance, created, **kwargs):
    """إرسال إشعار عند إنشاء دعوة جديدة"""
    if created:
        # يمكنك إضافة إشعارات ويب أو إشعارات داخل التطبيق هنا
        pass