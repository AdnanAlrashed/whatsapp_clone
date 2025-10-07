# whatsapp_clone/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
import os

def home(request):
    """الصفحة الرئيسية - تسجيل الدخول أو التسجيل"""
    if request.user.is_authenticated:
        return redirect('chat:home')  # إذا كان مسجل دخول، انتقل للدردشة
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # محاولة تسجيل الدخول
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            if user.is_active and user.is_email_verified:
                login(request, user)
                messages.success(request, 'تم تسجيل الدخول بنجاح!')
                return redirect('chat:home')
            elif not user.is_active:
                messages.error(request, 'حسابك غير مفعل. يرجى تفعيل حسابك أولاً.')
            elif not user.is_email_verified:
                messages.error(request, 'بريدك الإلكتروني غير مفعل. يرجى تفعيله أولاً.')
        else:
            messages.error(request, 'البريد الإلكتروني أو كلمة المرور غير صحيحة.')
    
    return render(request, 'home.html')

@csrf_exempt
def create_admin(request):
    """View طارئ لإنشاء superuser إذا فشل الإنشاء التلقائي"""
    if request.method == 'POST':
        try:
            User = get_user_model()
            
            if not User.objects.filter(is_superuser=True).exists():
                user = User.objects.create_superuser(
                    email='admin@whatsapp.com',
                    password='admin123456'
                )
                return JsonResponse({
                    'status': 'success',
                    'message': 'تم إنشاء superuser بنجاح',
                    'email': 'admin@whatsapp.com',
                    'password': 'admin123456'
                })
            else:
                return JsonResponse({
                    'status': 'info', 
                    'message': 'Superuser موجود بالفعل'
                })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'فشل الإنشاء: {str(e)}'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'استخدم POST request'
    })