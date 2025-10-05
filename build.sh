#!/usr/bin/env bash
# بناء التطبيق على Render مع تطبيق migrations قوي

echo "=== بدء عملية البناء ==="

# تثبيت الاعتماديات
echo "📦 تثبيت الاعتماديات..."
pip install -r requirements.txt

# جمع الملفات الثابتة
echo "📁 جمع الملفات الثابتة..."
python manage.py collectstatic --noinput --clear

# تطبيق migrations بشكل قوي ومنفصل
echo "🗃️ تطبيق تحديثات قاعدة البيانات..."

# أولاً: تطبيق migrations الأساسية
python manage.py migrate --noinput

# ثانياً: تطبيق migrations لكل تطبيق بشكل منفصل
echo "🔧 تطبيق migrations للتطبيقات..."
python manage.py migrate accounts --noinput
python manage.py migrate auth --noinput
python manage.py migrate contenttypes --noinput
python manage.py migrate sessions --noinput
python manage.py migrate admin --noinput
python manage.py migrate chat --noinput
python manage.py migrate calls --noinput

# التحقق من تطبيق migrations
echo "🔍 التحقق من migrations المطبقة..."
python manage.py showmigrations

# إنشاء superuser
echo "👑 إنشاء superuser..."
python manage.py shell << EOF
import os
from django.contrib.auth import get_user_model
User = get_user_model()

try:
    # حذف أي superuser موجود مسبقاً (للتأكد من الإنشاء)
    User.objects.filter(email='admin@whatsapp.com').delete()
    
    # إنشاء superuser جديد
    user = User.objects.create_superuser(
        email='admin@whatsapp.com',
        password='admin123456'
    )
    print('✅ تم إنشاء superuser بنجاح!')
    print('📧 البريد: admin@whatsapp.com')
    print('🔐 كلمة المرور: admin123456')
    print('🆔 User ID:', user.id)
except Exception as e:
    print(f'❌ فشل إنشاء superuser: {e}')
    import traceback
    traceback.print_exc()
EOF

echo "✅ اكتملت عملية البناء بنجاح!"