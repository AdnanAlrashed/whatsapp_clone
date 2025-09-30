# whatsapp_clone/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views  # استيراد الـ views من المجلد الحالي

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),  # الصفحة الرئيسية
    path('accounts/', include('accounts.urls')),
    path('chat/', include('chat.urls')),
    path('calls/', include('calls.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)