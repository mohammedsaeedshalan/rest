"""
إضافة بيانات تجريبية لنظام إدارة المطعم
هذا السكريبت يضيف بيانات تجريبية للاختبار
"""

from app import app, db, User, Item, Customer, Supplier
from werkzeug.security import generate_password_hash

def add_sample_data():
    with app.app_context():
        print("🚀 بدء إضافة البيانات التجريبية...")
        print()
        
        # التحقق من وجود بيانات
        if Item.query.count() > 0:
            print("⚠️  يوجد بيانات في النظام بالفعل")
            response = input("هل تريد حذف البيانات الموجودة وإضافة بيانات جديدة؟ (y/n): ")
            if response.lower() != 'y':
                print("❌ تم إلغاء العملية")
                return
            
            # حذف البيانات الموجودة
            print("🗑️  جاري حذف البيانات القديمة...")
            Item.query.delete()
            Customer.query.delete()
            Supplier.query.delete()
            db.session.commit()
        
        # إضافة أصناف تجريبية
        print("📦 إضافة الأصناف...")
        items = [
            Item(item_code='001', item_name='برجر لحم', category='وجبات رئيسية', quantity=50, price=25.00),
            Item(item_code='002', item_name='برجر دجاج', category='وجبات رئيسية', quantity=45, price=20.00),
            Item(item_code='003', item_name='بيتزا مارجريتا', category='بيتزا', quantity=30, price=35.00),
            Item(item_code='004', item_name='بيتزا بيبروني', category='بيتزا', quantity=25, price=40.00),
            Item(item_code='005', item_name='سلطة سيزر', category='سلطات', quantity=40, price=15.00),
            Item(item_code='006', item_name='سلطة يونانية', category='سلطات', quantity=35, price=18.00),
            Item(item_code='007', item_name='بطاطس مقلية', category='مقبلات', quantity=100, price=8.00),
            Item(item_code='008', item_name='أصابع الموزاريلا', category='مقبلات', quantity=60, price=12.00),
            Item(item_code='009', item_name='كولا', category='مشروبات', quantity=200, price=5.00),
            Item(item_code='010', item_name='عصير برتقال', category='مشروبات', quantity=150, price=7.00),
            Item(item_code='011', item_name='ماء معدني', category='مشروبات', quantity=300, price=3.00),
            Item(item_code='012', item_name='شاورما لحم', category='وجبات رئيسية', quantity=40, price=22.00),
            Item(item_code='013', item_name='شاورما دجاج', category='وجبات رئيسية', quantity=45, price=18.00),
            Item(item_code='014', item_name='فلافل', category='وجبات رئيسية', quantity=80, price=10.00),
            Item(item_code='015', item_name='حمص', category='مقبلات', quantity=50, price=8.00),
            Item(item_code='016', item_name='متبل', category='مقبلات', quantity=45, price=9.00),
            Item(item_code='017', item_name='فتوش', category='سلطات', quantity=30, price=12.00),
            Item(item_code='018', item_name='تبولة', category='سلطات', quantity=35, price=11.00),
            Item(item_code='019', item_name='كبسة دجاج', category='وجبات رئيسية', quantity=25, price=30.00),
            Item(item_code='020', item_name='كبسة لحم', category='وجبات رئيسية', quantity=20, price=35.00),
            Item(item_code='021', item_name='مندي دجاج', category='وجبات رئيسية', quantity=22, price=32.00),
            Item(item_code='022', item_name='مندي لحم', category='وجبات رئيسية', quantity=18, price=38.00),
            Item(item_code='023', item_name='كنافة', category='حلويات', quantity=15, price=20.00),
            Item(item_code='024', item_name='بسبوسة', category='حلويات', quantity=20, price=15.00),
            Item(item_code='025', item_name='أم علي', category='حلويات', quantity=18, price=18.00),
        ]
        
        for item in items:
            db.session.add(item)
        
        print(f"   ✅ تم إضافة {len(items)} صنف")
        
        # إضافة عملاء تجريبيين
        print("👥 إضافة العملاء...")
        customers = [
            Customer(customer_code='C001', customer_name='أحمد محمد', address='الرياض - حي النخيل', phone='0501234567', balance=0),
            Customer(customer_code='C002', customer_name='فاطمة علي', address='جدة - حي الصفا', phone='0551234567', balance=0),
            Customer(customer_code='C003', customer_name='محمد عبدالله', address='الدمام - حي الفيصلية', phone='0561234567', balance=0),
            Customer(customer_code='C004', customer_name='نورة سعد', address='الرياض - حي العليا', phone='0571234567', balance=0),
            Customer(customer_code='C005', customer_name='خالد إبراهيم', address='مكة - حي العزيزية', phone='0581234567', balance=0),
            Customer(customer_code='C006', customer_name='سارة حسن', address='المدينة - حي السلام', phone='0591234567', balance=0),
            Customer(customer_code='C007', customer_name='عبدالرحمن أحمد', address='الرياض - حي الملقا', phone='0501111111', balance=0),
            Customer(customer_code='C008', customer_name='مريم عمر', address='جدة - حي الروضة', phone='0552222222', balance=0),
            Customer(customer_code='C009', customer_name='يوسف سالم', address='الخبر - حي الثقبة', phone='0563333333', balance=0),
            Customer(customer_code='C010', customer_name='هند ناصر', address='الرياض - حي الياسمين', phone='0574444444', balance=0),
        ]
        
        for customer in customers:
            db.session.add(customer)
        
        print(f"   ✅ تم إضافة {len(customers)} عميل")
        
        # إضافة موردين تجريبيين
        print("🚚 إضافة الموردين...")
        suppliers = [
            Supplier(supplier_code='S001', supplier_name='مؤسسة الطازج للخضروات', address='الرياض - سوق الخضار المركزي', phone='0112345678', balance=0),
            Supplier(supplier_code='S002', supplier_name='شركة اللحوم الوطنية', address='الرياض - المنطقة الصناعية', phone='0112345679', balance=0),
            Supplier(supplier_code='S003', supplier_name='مصنع الألبان الطازجة', address='الخرج - المنطقة الصناعية', phone='0112345680', balance=0),
            Supplier(supplier_code='S004', supplier_name='مخبز الأفران الذهبية', address='الرياض - حي الشفا', phone='0112345681', balance=0),
            Supplier(supplier_code='S005', supplier_name='شركة المشروبات الباردة', address='جدة - المنطقة الصناعية', phone='0122345678', balance=0),
            Supplier(supplier_code='S006', supplier_name='مؤسسة التوابل والبهارات', address='الرياض - سوق البهارات', phone='0112345682', balance=0),
            Supplier(supplier_code='S007', supplier_name='شركة الدواجن الطازجة', address='الدمام - المنطقة الصناعية', phone='0132345678', balance=0),
        ]
        
        for supplier in suppliers:
            db.session.add(supplier)
        
        print(f"   ✅ تم إضافة {len(suppliers)} مورد")
        
        # إضافة مستخدمين إضافيين
        print("👤 إضافة مستخدمين...")

        # التحقق من عدم وجود المستخدمين
        existing_users = ['admin', 'manager1', 'user1']
        users_to_add = []

        if not User.query.filter_by(username='manager1').first():
            manager = User(username='manager1', full_name='مدير المطعم',
                          role='manager', is_active=True)
            manager.set_password('manager123')
            users_to_add.append(manager)

        if not User.query.filter_by(username='user1').first():
            user = User(username='user1', full_name='موظف المبيعات',
                       role='user', is_active=True)
            user.set_password('user123')
            users_to_add.append(user)

        for user in users_to_add:
            db.session.add(user)
        
        if users_to_add:
            print(f"   ✅ تم إضافة {len(users_to_add)} مستخدم")
        else:
            print("   ℹ️  المستخدمون موجودون بالفعل")
        
        # حفظ جميع التغييرات
        db.session.commit()
        
        print()
        print("═══════════════════════════════════════════════════════════════")
        print("✅ تم إضافة البيانات التجريبية بنجاح!")
        print("═══════════════════════════════════════════════════════════════")
        print()
        print("📊 ملخص البيانات المضافة:")
        print(f"   • الأصناف: {len(items)}")
        print(f"   • العملاء: {len(customers)}")
        print(f"   • الموردين: {len(suppliers)}")
        print(f"   • المستخدمين: {len(users_to_add)}")
        print()
        print("🔐 بيانات الدخول المتاحة:")
        print("   1. المدير:")
        print("      المستخدم: admin")
        print("      كلمة المرور: admin123")
        print()
        print("   2. المشرف:")
        print("      المستخدم: manager1")
        print("      كلمة المرور: manager123")
        print()
        print("   3. المستخدم:")
        print("      المستخدم: user1")
        print("      كلمة المرور: user123")
        print()
        print("═══════════════════════════════════════════════════════════════")
        print()

if __name__ == '__main__':
    add_sample_data()

