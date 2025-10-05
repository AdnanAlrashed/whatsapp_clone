#!/usr/bin/env bash
# بناء التطبيق على Render

echo "=== بدء عملية البناء ==="

# تثبيت الاعتماديات
echo "📦 تثبيت الاعتماديات..."
pip install -r requirements.txt

# جمع الملفات الثابتة
echo "📁 جمع الملفات الثابتة..."
python manage.py collectstatic --noinput

# تطبيق migrations بشكل منفصل لكل تطبيق
echo "🗃️ تطبيق تحديثات قاعدة البيانات..."
python manage.py migrate --noinput
python manage.py migrate accounts --noinput
python manage.py migrate chat --noinput  
python manage.py migrate calls --noinput

# التحقق من تطبيق migrations
echo "🔍 التحقق من تطبيق migrations..."
python manage.py showmigrations

# إنشاء superuser إذا لم يكن موجوداً
echo "👑 التحقق من وجود superuser..."
python manage.py shell << EOF
import os
from django.contrib.auth import get_user_model
User = get_user_model()

try:
    if not User.objects.filter(email='admin@whatsapp.com').exists():
        print('🔄 إنشاء superuser جديد...')
        user = User.objects.create_superuser(
            email='admin@whatsapp.com',
            password='admin123456'
        )
        print('✅ تم إنشاء superuser بنجاح!')
        print('📧 البريد: admin@whatsapp.com')
        print('🔐 كلمة المرور: admin123456')
    else:
        print('✅ Superuser موجود بالفعل')
except Exception as e:
    print(f'❌ فشل إنشاء superuser: {e}')
EOF

echo "✅ اكتملت عملية البناء بنجاح!"