#!/usr/bin/env bash
# بناء التطبيق على Render مع إنشاء superuser

echo "=== بدء عملية البناء ==="

# تثبيت الاعتماديات
echo "📦 تثبيت الاعتماديات..."
pip install -r requirements.txt

# جمع الملفات الثابتة
echo "📁 جمع الملفات الثابتة..."
python manage.py collectstatic --noinput

# تطبيق migrations
echo "🗃️ تطبيق تحديثات قاعدة البيانات..."
python manage.py migrate --noinput

# إنشاء superuser إذا لم يكن موجوداً
echo "👑 التحقق من وجود superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(email='admin@whatsapp.com').exists():
    print("🔄 إنشاء superuser جديد...")
    User.objects.create_superuser(
        email='admin@whatsapp.com',
        password='admin123456',
        is_active=True,
        is_staff=True,
        is_superuser=True
    )
    print("✅ تم إنشاء superuser بنجاح!")
    print("📧 البريد: admin@whatsapp.com")
    print("🔐 كلمة المرور: admin123456")
else:
    print("✅ Superuser موجود بالفعل")
EOF

echo "✅ اكتملت عملية البناء بنجاح!"