@echo off
chcp 65001 >nul
cls
echo ═══════════════════════════════════════════════════════════════
echo                    نظام إدارة المطعم
echo ═══════════════════════════════════════════════════════════════
echo.
echo 🚀 جاري تشغيل النظام...
echo.

REM التحقق من وجود Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ خطأ: Python غير مثبت على النظام
    echo.
    echo يرجى تثبيت Python من: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM التحقق من تثبيت المكتبات
echo 📦 التحقق من المكتبات المطلوبة...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  المكتبات غير مثبتة. جاري التثبيت...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ❌ فشل تثبيت المكتبات
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ✅ جميع المتطلبات متوفرة
echo.
echo ═══════════════════════════════════════════════════════════════
echo.
echo 🌐 سيتم فتح التطبيق على: http://localhost:5000
echo.
echo 🔐 بيانات الدخول الافتراضية:
echo    المستخدم: admin
echo    كلمة المرور: admin123
echo.
echo ═══════════════════════════════════════════════════════════════
echo.
echo 💡 لإيقاف الخادم اضغط Ctrl+C
echo.
echo ═══════════════════════════════════════════════════════════════
echo.

REM تشغيل التطبيق
python app.py

echo.
echo.
echo ═══════════════════════════════════════════════════════════════
echo              تم إيقاف الخادم
echo ═══════════════════════════════════════════════════════════════
echo.
pause

