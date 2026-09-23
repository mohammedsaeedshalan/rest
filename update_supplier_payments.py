#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
سكريبت لتحديث قاعدة البيانات - إضافة جدول دفعات الموردين
"""

from app import app, db

def update_database():
    """تحديث قاعدة البيانات بإضافة الجداول الجديدة"""
    with app.app_context():
        try:
            print("🔄 جاري تحديث قاعدة البيانات...")
            
            # إنشاء جميع الجداول (سيتم إنشاء الجداول الجديدة فقط)
            db.create_all()
            
            print("✅ تم تحديث قاعدة البيانات بنجاح!")
            print("✅ تم إضافة جدول دفعات الموردين (supplier_payments)")
            
        except Exception as e:
            print(f"❌ حدث خطأ أثناء التحديث: {str(e)}")
            return False
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("تحديث قاعدة البيانات - نظام إدارة المطعم")
    print("=" * 60)
    
    if update_database():
        print("\n" + "=" * 60)
        print("✅ اكتمل التحديث بنجاح!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ فشل التحديث!")
        print("=" * 60)

