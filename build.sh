#!/usr/bin/env bash
# بناء التطبيق على Render

echo "=== بدء عملية البناء ==="

# تثبيت الاعتماديات
echo "📦 تثبيت الاعتماديات..."
pip install -r requirements.txt

# جمع الملفات الثابتة
echo "📁 جمع الملفات الثابتة..."
python manage.py collectstatic --noinput

# تطبيق migrations
echo "🗃️ تطبيق تحديثات قاعدة البيانات..."
python manage.py migrate

echo "✅ اكتملت عملية البناء بنجاح!"