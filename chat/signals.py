# في chat/signals.py - إنشاء ملف جديد
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import user_logged_in, user_logged_out
from .models import OnlineUser, ChatRoom

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """عند تسجيل دخول المستخدم"""
    try:
        # يمكنك هنا تحديث حالة الاتصال للغرف النشطة
        print(f"User {user.email} logged in")
    except Exception as e:
        print(f"Error in user_logged_in_handler: {e}")

@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """عند تسجيل خروج المستخدم"""
    try:
        # تحديث جميع سجلات OnlineUser لهذا المستخدم
        OnlineUser.objects.filter(user=user).update(is_online=False)
        print(f"User {user.email} logged out - marked as offline in all rooms")
    except Exception as e:
        print(f"Error in user_logged_out_handler: {e}")

# تأكد من تسجيل الإشارات في apps.py