# whatsapp_clone/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def home(request):
    """الصفحة الرئيسية - تسجيل الدخول أو التسجيل"""
    if request.user.is_authenticated:
        return redirect('chat:room')  # إذا كان مسجل دخول، انتقل للدردشة
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # محاولة تسجيل الدخول
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, 'تم تسجيل الدخول بنجاح!')
                return redirect('chat:room')
            else:
                messages.error(request, 'حسابك غير مفعل. يرجى تفعيل حسابك أولاً.')
        else:
            messages.error(request, 'البريد الإلكتروني أو كلمة المرور غير صحيحة.')
    
    return render(request, 'home.html')