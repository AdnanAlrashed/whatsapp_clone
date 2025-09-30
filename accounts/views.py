from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import EmailMessage, BadHeaderError
from smtplib import SMTPException
from django.contrib import messages
from .forms import SignUpForm
from .tokens import account_activation_token
from .models import CustomUser

from django.contrib.auth import login
from django.shortcuts import redirect

def signup(request):
    if request.user.is_authenticated:
        return redirect('chat:room')  # إذا كان مسجل دخول، انتقل للدردشة
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            
            print(f"✅ USER CREATED - ID: {user.pk}, Email: {user.email}")
            
            # استخدام base64 encoding بشكل صحيح
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)
            
            print(f"Encoded UID: {uid}")
            print(f"Token: {token}")
            
            current_site = get_current_site(request)
            mail_subject = 'تفعيل حسابك في نظام الدردشة'
            message = render_to_string('accounts/activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': uid,
                'token': token,
                'protocol': 'https' if request.is_secure() else 'http'
            })
            
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            
            try:
                email.send()
                print(f"✅ ACTIVATION EMAIL SENT TO: {to_email}")
                messages.success(request, 'تم إرسال بريد التفعيل إلى بريدك الإلكتروني.')
                return redirect('accounts:account_activation_sent')
            except Exception as e:
                # ❌ إزالة user.delete() - لا تحذف المستخدم عند فشل الإرسال
                print(f"❌ EMAIL SENDING FAILED: {str(e)}")
                messages.error(request, f'حدث خطأ في إرسال بريد التفعيل: {str(e)}. يرجى المحاولة لاحقاً أو التواصل مع الدعم.')
                # يمكنك اختيارياً إضافة إعادة إرسال البريد لاحقاً
                return render(request, 'accounts/signup.html', {'form': form})
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})

def send_activation_email(user, request):
    """دالة لإرسال بريد التفعيل"""
    current_site = get_current_site(request)
    mail_subject = 'تفعيل حسابك في نظام الدردشة'
    
    # رسالة البريد الإلكتروني
    message = render_to_string('accounts/activation_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    
    to_email = user.email
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.send()

def send_welcome_email(user):
    """دالة لإرسال بريد ترحيب بعد التفعيل"""
    welcome_subject = 'مرحباً بك في نظام الدردشة!'
    welcome_message = f"""
    مرحباً {user.email},
    
    تم تفعيل حسابك بنجاح في نظام الدردشة.
    
    يمكنك الآن تسجيل الدخول والاستمتاع بميزات النظام:
    - الدردشة الفورية
    - المكالمات الصوتية والمرئية
    - مشاركة الصور والملفات
    
    شكراً لانضمامك إلينا!
    
    فريق الدعم الفني
    """
    
    email = EmailMessage(welcome_subject, welcome_message, to=[user.email])
    email.send()

def activate(request, uidb64, token):
    print(f"=== ACTIVATION ATTEMPT ===")
    print(f"Received UID: {uidb64}")
    print(f"Received token: {token}")
    
    try:
        # فك التشفير
        uid = force_str(urlsafe_base64_decode(uidb64))
        user_id = int(uid)
        print(f"Decoded UID: {uid}, User ID: {user_id}")
        
        # فحص وجود المستخدم
        try:
            user = CustomUser.objects.get(pk=user_id)
            print(f"✅ User found: {user.email} (ID: {user.pk})")
            print(f"User status - Active: {user.is_active}, Verified: {user.is_email_verified}")
        except CustomUser.DoesNotExist:
            print(f"❌ User with ID {user_id} does not exist")
            messages.error(request, 'المستخدم غير موجود. يرجى التسجيل مرة أخرى.')
            return render(request, 'accounts/activation_invalid.html')
        
        # التحقق من التوكن
        if account_activation_token.check_token(user, token):
            if user.is_active:
                print("ℹ️ User already active")
                messages.info(request, 'حسابك مفعل بالفعل. يمكنك تسجيل الدخول.')
            else:
                user.is_active = True
                user.is_email_verified = True
                user.save()
                print("✅ User activated successfully")
                
                # إرسال بريد ترحيبي
                try:
                    send_welcome_email(user)
                    print("✅ Welcome email sent")
                except Exception as e:
                    print(f"⚠️ Welcome email failed: {e}")
                
                messages.success(request, 'تم تفعيل حسابك بنجاح! مرحباً بك!')
            
            # تسجيل الدخول
            login(request, user)
            print("✅ User logged in successfully")
            return redirect('chat/room')  # تأكد من وجود هذا المسار
            
        else:
            print("❌ Invalid token")
            messages.error(request, 'رابط التفعيل غير صالح أو منتهي الصلاحية.')
            
    except (TypeError, ValueError, OverflowError) as e:
        print(f"❌ Decoding error: {e}")
        messages.error(request, 'رابط التفعيل تالف.')
    
    return render(request, 'accounts/activation_invalid.html')


def account_activation_sent(request):
    """صفحة تأكيد إرسال بريد التفعيل"""
    return render(request, 'accounts/account_activation_sent.html')

def resend_activation(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email, is_active=False)
            send_activation_email(user, request)
            messages.success(request, 'تم إعادة إرسال بريد التفعيل.')
            return redirect('accounts:account_activation_sent')
        except CustomUser.DoesNotExist:
            messages.error(request, 'لم يتم العثور على حساب غير مفعل بهذا البريد.')
    
    return render(request, 'accounts/resend_activation.html')