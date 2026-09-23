from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
from functools import wraps
import os
from sqlalchemy import inspect, text

app = Flask(__name__)
database_url = os.getenv('DATABASE_URL', 'sqlite:///restaurant.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # admin, manager, user
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), unique=True, nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, default=0)
    min_quantity = db.Column(db.Float, default=5, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    customer_code = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    balance = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    supplier_code = db.Column(db.String(50), unique=True, nullable=False)
    supplier_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    balance = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    sale_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # cash, card, credit
    paid_amount = db.Column(db.Float, default=0)
    remaining_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='completed')  # completed, pending, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    customer = db.relationship('Customer', backref='sales')
    user = db.relationship('User', backref='sales')
    items = db.relationship('SaleItem', backref='sale', cascade='all, delete-orphan')

class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    
    item = db.relationship('Item')

class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    purchase_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    paid_amount = db.Column(db.Float, default=0)
    remaining_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='completed')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    supplier = db.relationship('Supplier', backref='purchases')
    user = db.relationship('User', backref='purchases')
    items = db.relationship('PurchaseItem', backref='purchase', cascade='all, delete-orphan')

class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)

    item = db.relationship('Item')

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    payment_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # cash, card, bank_transfer
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship('Customer', backref='payments')
    user = db.relationship('User', backref='payments')

class SupplierPayment(db.Model):
    __tablename__ = 'supplier_payments'
    id = db.Column(db.Integer, primary_key=True)
    payment_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # cash, card, bank_transfer
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    supplier = db.relationship('Supplier', backref='supplier_payments')
    user = db.relationship('User', backref='supplier_payments')

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    employee_name = db.Column(db.String(100), nullable=False)
    nationality = db.Column(db.String(80), nullable=False)
    monthly_salary = db.Column(db.Float, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SalaryPayment(db.Model):
    __tablename__ = 'salary_payments'
    id = db.Column(db.Integer, primary_key=True)
    payment_number = db.Column(db.String(50), unique=True, nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_month = db.Column(db.String(7), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False, default='cash')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', backref='salary_payments')
    user = db.relationship('User', backref='salary_payments')

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    expense_number = db.Column(db.String(50), unique=True, nullable=False)
    expense_date = db.Column(db.Date, nullable=False, default=date.today)
    category = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False, default='cash')
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='expenses')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'manager']:
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
@login_required
def index():
    # Dashboard statistics
    total_sales = db.session.query(db.func.sum(Sale.total_amount)).filter(
        Sale.status == 'completed'
    ).scalar() or 0
    
    total_purchases = db.session.query(db.func.sum(Purchase.total_amount)).filter(
        Purchase.status == 'completed'
    ).scalar() or 0

    total_salary_payments = db.session.query(db.func.sum(SalaryPayment.amount)).scalar() or 0
    total_expenses = db.session.query(db.func.sum(Expense.amount)).scalar() or 0
    net_profit = total_sales - total_purchases - total_salary_payments - total_expenses
    
    total_customers = Customer.query.count()
    total_suppliers = Supplier.query.count()
    total_items = Item.query.count()
    low_stock_items = Item.query.filter(Item.quantity <= Item.min_quantity).order_by(
        Item.quantity.asc()
    ).all()

    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()

    return render_template('index.html',
                         total_sales=total_sales,
                         total_purchases=total_purchases,
                         total_salary_payments=total_salary_payments,
                         total_expenses=total_expenses,
                         net_profit=net_profit,
                         total_customers=total_customers,
                         total_suppliers=total_suppliers,
                         total_items=total_items,
                         low_stock_items=low_stock_items,
                         recent_sales=recent_sales)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip().lower()
        password = request.form.get('password') or ''
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash('تم تسجيل الدخول بنجاح', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))

# Items Management
@app.route('/items')
@login_required
def items():
    items_list = Item.query.order_by(Item.created_at.desc()).all()
    return render_template('items.html', items=items_list)

@app.route('/items/add', methods=['POST'])
@login_required
def add_item():
    try:
        item = Item(
            item_code=request.form.get('item_code'),
            item_name=request.form.get('item_name'),
            quantity=float(request.form.get('quantity', 0)),
            min_quantity=float(request.form.get('min_quantity', 5)),
            price=float(request.form.get('price')),
            category=request.form.get('category'),
            description=request.form.get('description')
        )
        db.session.add(item)
        db.session.commit()
        flash('تم إضافة الصنف بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('items'))

@app.route('/items/edit/<int:id>', methods=['POST'])
@login_required
def edit_item(id):
    try:
        item = Item.query.get_or_404(id)
        item.item_code = request.form.get('item_code')
        item.item_name = request.form.get('item_name')
        item.quantity = float(request.form.get('quantity', 0))
        item.min_quantity = float(request.form.get('min_quantity', 5))
        item.price = float(request.form.get('price'))
        item.category = request.form.get('category')
        item.description = request.form.get('description')
        db.session.commit()
        flash('تم تعديل الصنف بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('items'))

@app.route('/items/delete/<int:id>')
@login_required
@manager_required
def delete_item(id):
    try:
        item = Item.query.get_or_404(id)
        db.session.delete(item)
        db.session.commit()
        flash('تم حذف الصنف بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('items'))

# Customers Management
@app.route('/customers')
@login_required
def customers():
    customers_list = Customer.query.order_by(Customer.created_at.desc()).all()
    return render_template('customers.html', customers=customers_list)

@app.route('/customers/add', methods=['POST'])
@login_required
def add_customer():
    try:
        customer = Customer(
            customer_code=request.form.get('customer_code'),
            customer_name=request.form.get('customer_name'),
            address=request.form.get('address'),
            phone=request.form.get('phone')
        )
        db.session.add(customer)
        db.session.commit()
        flash('تم إضافة العميل بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('customers'))

@app.route('/customers/edit/<int:id>', methods=['POST'])
@login_required
def edit_customer(id):
    try:
        customer = Customer.query.get_or_404(id)
        customer.customer_code = request.form.get('customer_code')
        customer.customer_name = request.form.get('customer_name')
        customer.address = request.form.get('address')
        customer.phone = request.form.get('phone')
        db.session.commit()
        flash('تم تعديل العميل بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('customers'))

@app.route('/customers/delete/<int:id>')
@login_required
@manager_required
def delete_customer(id):
    try:
        customer = Customer.query.get_or_404(id)
        db.session.delete(customer)
        db.session.commit()
        flash('تم حذف العميل بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('customers'))

# Customer Payments
@app.route('/customers/<int:customer_id>/payments', methods=['GET'])
@login_required
def customer_payments(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    payments = Payment.query.filter_by(customer_id=customer_id).order_by(Payment.created_at.desc()).all()
    return render_template('customer_payments.html', customer=customer, payments=payments)

@app.route('/customers/<int:customer_id>/payments/add', methods=['POST'])
@login_required
def add_payment(customer_id):
    try:
        customer = Customer.query.get_or_404(customer_id)
        amount = float(request.form.get('amount'))

        # Generate payment number
        last_payment = Payment.query.order_by(Payment.id.desc()).first()
        payment_number = f'PAY{(last_payment.id + 1):05d}' if last_payment else 'PAY00001'

        payment = Payment(
            payment_number=payment_number,
            customer_id=customer_id,
            user_id=current_user.id,
            amount=amount,
            payment_method=request.form.get('payment_method'),
            notes=request.form.get('notes')
        )

        # Update customer balance (subtract payment from debt)
        customer.balance -= amount

        db.session.add(payment)
        db.session.commit()
        flash('تم إضافة الدفعة بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('customer_payments', customer_id=customer_id))

# Supplier Payments
@app.route('/suppliers/<int:supplier_id>/payments', methods=['GET'])
@login_required
def supplier_payments(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    payments = SupplierPayment.query.filter_by(supplier_id=supplier_id).order_by(SupplierPayment.created_at.desc()).all()
    return render_template('supplier_payments.html', supplier=supplier, payments=payments)

@app.route('/suppliers/<int:supplier_id>/payments/add', methods=['POST'])
@login_required
def add_supplier_payment(supplier_id):
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        amount = float(request.form.get('amount'))

        # Generate payment number
        last_payment = SupplierPayment.query.order_by(SupplierPayment.id.desc()).first()
        payment_number = f'SPAY{(last_payment.id + 1):05d}' if last_payment else 'SPAY00001'

        payment = SupplierPayment(
            payment_number=payment_number,
            supplier_id=supplier_id,
            user_id=current_user.id,
            amount=amount,
            payment_method=request.form.get('payment_method'),
            notes=request.form.get('notes')
        )

        # Update supplier balance (subtract payment from debt)
        supplier.balance -= amount

        db.session.add(payment)
        db.session.commit()
        flash('تم إضافة الدفعة بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('supplier_payments', supplier_id=supplier_id))

# Suppliers Management
@app.route('/suppliers')
@login_required
def suppliers():
    suppliers_list = Supplier.query.order_by(Supplier.created_at.desc()).all()
    return render_template('suppliers.html', suppliers=suppliers_list)

@app.route('/suppliers/add', methods=['POST'])
@login_required
def add_supplier():
    try:
        supplier = Supplier(
            supplier_code=request.form.get('supplier_code'),
            supplier_name=request.form.get('supplier_name'),
            address=request.form.get('address'),
            phone=request.form.get('phone')
        )
        db.session.add(supplier)
        db.session.commit()
        flash('تم إضافة المورد بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('suppliers'))

@app.route('/suppliers/edit/<int:id>', methods=['POST'])
@login_required
def edit_supplier(id):
    try:
        supplier = Supplier.query.get_or_404(id)
        supplier.supplier_code = request.form.get('supplier_code')
        supplier.supplier_name = request.form.get('supplier_name')
        supplier.address = request.form.get('address')
        supplier.phone = request.form.get('phone')
        db.session.commit()
        flash('تم تعديل المورد بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('suppliers'))

@app.route('/suppliers/delete/<int:id>')
@login_required
@manager_required
def delete_supplier(id):
    try:
        supplier = Supplier.query.get_or_404(id)
        db.session.delete(supplier)
        db.session.commit()
        flash('تم حذف المورد بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('suppliers'))

# Employees and Salary Payments
@app.route('/employees')
@login_required
def employees():
    employees_list = Employee.query.order_by(Employee.created_at.desc()).all()
    return render_template('employees.html', employees=employees_list)

@app.route('/employees/add', methods=['POST'])
@login_required
def add_employee():
    try:
        employee = Employee(
            employee_name=request.form.get('employee_name'),
            nationality=request.form.get('nationality'),
            monthly_salary=float(request.form.get('monthly_salary', 0))
        )
        db.session.add(employee)
        db.session.commit()
        flash('تم إضافة العامل بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('employees'))

@app.route('/employees/edit/<int:id>', methods=['POST'])
@login_required
def edit_employee(id):
    try:
        employee = Employee.query.get_or_404(id)
        employee.employee_name = request.form.get('employee_name')
        employee.nationality = request.form.get('nationality')
        employee.monthly_salary = float(request.form.get('monthly_salary', 0))
        db.session.commit()
        flash('تم تعديل بيانات العامل بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('employees'))

@app.route('/employees/delete/<int:id>')
@login_required
@manager_required
def delete_employee(id):
    try:
        employee = Employee.query.get_or_404(id)
        db.session.delete(employee)
        db.session.commit()
        flash('تم حذف العامل بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('employees'))

@app.route('/employees/<int:employee_id>/salary-payments')
@login_required
def salary_payments(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    payments = SalaryPayment.query.filter_by(employee_id=employee_id).order_by(
        SalaryPayment.payment_month.desc(), SalaryPayment.created_at.desc()
    ).all()
    return render_template('salary_payments.html', employee=employee, payments=payments)

@app.route('/employees/<int:employee_id>/salary-payments/add', methods=['POST'])
@login_required
def add_salary_payment(employee_id):
    try:
        Employee.query.get_or_404(employee_id)
        last_payment = SalaryPayment.query.order_by(SalaryPayment.id.desc()).first()
        payment_number = f'SAL{(last_payment.id + 1):05d}' if last_payment else 'SAL00001'
        payment = SalaryPayment(
            payment_number=payment_number,
            employee_id=employee_id,
            user_id=current_user.id,
            amount=float(request.form.get('amount')),
            payment_month=request.form.get('payment_month'),
            payment_method=request.form.get('payment_method'),
            notes=request.form.get('notes')
        )
        db.session.add(payment)
        db.session.commit()
        flash('تم تسجيل دفعة الراتب بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('salary_payments', employee_id=employee_id))

@app.route('/salary-payments/edit/<int:id>', methods=['POST'])
@login_required
def edit_salary_payment(id):
    payment = SalaryPayment.query.get_or_404(id)
    employee_id = payment.employee_id
    try:
        payment.amount = float(request.form.get('amount'))
        payment.payment_month = request.form.get('payment_month')
        payment.payment_method = request.form.get('payment_method')
        payment.notes = request.form.get('notes')
        db.session.commit()
        flash('تم تعديل دفعة الراتب بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('salary_payments', employee_id=employee_id))

@app.route('/salary-payments/delete/<int:id>', methods=['POST'])
@login_required
@manager_required
def delete_salary_payment(id):
    payment = SalaryPayment.query.get_or_404(id)
    employee_id = payment.employee_id
    try:
        db.session.delete(payment)
        db.session.commit()
        flash('تم حذف دفعة الراتب بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('salary_payments', employee_id=employee_id))

# Daily Expenses
@app.route('/expenses')
@login_required
def expenses():
    selected_date = request.args.get('expense_date') or date.today().isoformat()
    try:
        expense_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        expense_date = date.today()
        selected_date = expense_date.isoformat()

    expenses_list = Expense.query.filter_by(expense_date=expense_date).order_by(
        Expense.created_at.desc()
    ).all()
    total = sum(expense.amount for expense in expenses_list)
    return render_template('expenses.html', expenses=expenses_list, total=total,
                           selected_date=selected_date)

@app.route('/expenses/add', methods=['POST'])
@login_required
def add_expense():
    try:
        expense_date = datetime.strptime(
            request.form.get('expense_date') or date.today().isoformat(), '%Y-%m-%d'
        ).date()
        amount = float(request.form.get('amount'))
        if amount <= 0:
            raise ValueError('يجب أن يكون المبلغ أكبر من صفر')

        last_expense = Expense.query.order_by(Expense.id.desc()).first()
        expense_number = f'EXP{(last_expense.id + 1):05d}' if last_expense else 'EXP00001'
        expense = Expense(
            expense_number=expense_number,
            expense_date=expense_date,
            category=(request.form.get('category') or '').strip(),
            amount=amount,
            payment_method=request.form.get('payment_method') or 'cash',
            notes=request.form.get('notes'),
            user_id=current_user.id
        )
        if not expense.category:
            raise ValueError('يرجى تحديد بند المصروف')

        db.session.add(expense)
        db.session.commit()
        flash('تم تسجيل المصروف بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('expenses', expense_date=request.form.get('expense_date')))

@app.route('/expenses/delete/<int:id>')
@login_required
@manager_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    expense_date = expense.expense_date.isoformat()
    try:
        db.session.delete(expense)
        db.session.commit()
        flash('تم حذف المصروف بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('expenses', expense_date=expense_date))

# Purchases Management
@app.route('/purchases')
@login_required
def purchases():
    items_list = Item.query.all()
    suppliers_list = Supplier.query.all()

    # تجميع الأصناف حسب التصنيف
    categories = {}
    for item in items_list:
        category = item.category if item.category else 'غير مصنف'
        if category not in categories:
            categories[category] = []
        categories[category].append(item)

    return render_template('purchases.html', items=items_list, suppliers=suppliers_list, categories=categories)

@app.route('/purchases/create', methods=['POST'])
@login_required
def create_purchase():
    try:
        data = request.get_json()

        # Generate purchase number
        last_purchase = Purchase.query.order_by(Purchase.id.desc()).first()
        purchase_number = f"PUR-{(last_purchase.id + 1) if last_purchase else 1:06d}"

        # Create purchase
        purchase = Purchase(
            purchase_number=purchase_number,
            supplier_id=data.get('supplier_id'),
            user_id=current_user.id,
            total_amount=float(data.get('total_amount')),
            paid_amount=float(data.get('paid_amount', 0)),
            remaining_amount=float(data.get('remaining_amount', 0)),
            notes=data.get('notes')
        )
        db.session.add(purchase)
        db.session.flush()

        # Add purchase items and update inventory
        for item_data in data.get('items', []):
            purchase_item = PurchaseItem(
                purchase_id=purchase.id,
                item_id=item_data['item_id'],
                quantity=float(item_data['quantity']),
                price=float(item_data['price']),
                total=float(item_data['total'])
            )
            db.session.add(purchase_item)

            # Update item quantity (add to inventory)
            item = Item.query.get(item_data['item_id'])
            item.quantity += float(item_data['quantity'])

        # Update supplier balance if there's remaining amount
        if float(data.get('remaining_amount', 0)) > 0:
            supplier = Supplier.query.get(data.get('supplier_id'))
            supplier.balance += float(data.get('remaining_amount', 0))

        db.session.commit()
        return jsonify({'success': True, 'purchase_number': purchase_number})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# Sales (POS)
@app.route('/sales')
@login_required
def sales():
    items_list = Item.query.filter(Item.quantity > 0).all()
    customers_list = Customer.query.all()

    # تجميع الأصناف حسب التصنيف
    categories = {}
    for item in items_list:
        category = item.category if item.category else 'غير مصنف'
        if category not in categories:
            categories[category] = []
        categories[category].append(item)

    return render_template('sales.html', items=items_list, customers=customers_list, categories=categories)

@app.route('/sales/create', methods=['POST'])
@login_required
def create_sale():
    try:
        data = request.get_json()

        # Generate sale number
        last_sale = Sale.query.order_by(Sale.id.desc()).first()
        sale_number = f"INV-{(last_sale.id + 1) if last_sale else 1:06d}"

        # Create sale
        sale = Sale(
            sale_number=sale_number,
            customer_id=data.get('customer_id') if data.get('customer_id') else None,
            user_id=current_user.id,
            total_amount=float(data.get('total_amount')),
            payment_method=data.get('payment_method'),
            paid_amount=float(data.get('paid_amount', 0)),
            remaining_amount=float(data.get('remaining_amount', 0)),
            notes=data.get('notes')
        )
        db.session.add(sale)
        db.session.flush()

        # Add sale items and update inventory
        for item_data in data.get('items', []):
            sale_item = SaleItem(
                sale_id=sale.id,
                item_id=item_data['item_id'],
                quantity=float(item_data['quantity']),
                price=float(item_data['price']),
                total=float(item_data['total'])
            )
            db.session.add(sale_item)

            # Update item quantity
            item = Item.query.get(item_data['item_id'])
            item.quantity -= float(item_data['quantity'])

        # Update customer balance if credit sale
        if data.get('payment_method') == 'credit' and data.get('customer_id'):
            customer = Customer.query.get(data.get('customer_id'))
            customer.balance += float(data.get('remaining_amount', 0))

        db.session.commit()
        return jsonify({'success': True, 'sale_number': sale_number})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/sales/hold', methods=['POST'])
@login_required
def hold_sale():
    try:
        data = request.get_json()

        last_sale = Sale.query.order_by(Sale.id.desc()).first()
        sale_number = f"HOLD-{(last_sale.id + 1) if last_sale else 1:06d}"

        sale = Sale(
            sale_number=sale_number,
            customer_id=data.get('customer_id') if data.get('customer_id') else None,
            user_id=current_user.id,
            total_amount=float(data.get('total_amount')),
            payment_method=data.get('payment_method'),
            paid_amount=float(data.get('paid_amount', 0)),
            remaining_amount=float(data.get('remaining_amount', 0)),
            status='pending',
            notes=data.get('notes')
        )
        db.session.add(sale)
        db.session.flush()

        for item_data in data.get('items', []):
            sale_item = SaleItem(
                sale_id=sale.id,
                item_id=item_data['item_id'],
                quantity=float(item_data['quantity']),
                price=float(item_data['price']),
                total=float(item_data['total'])
            )
            db.session.add(sale_item)

        if data.get('payment_method') == 'credit' and data.get('customer_id'):
            customer = Customer.query.get(data.get('customer_id'))
            if customer:
                customer.balance += float(data.get('remaining_amount', 0))

        db.session.commit()
        return jsonify({'success': True, 'sale_number': sale_number, 'sale_id': sale.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/sales/held', methods=['GET'])
@login_required
def get_held_sales():
    sales = Sale.query.filter_by(status='pending').order_by(Sale.created_at.desc()).all()
    result = []

    for sale in sales:
        item_data = []
        for sale_item in sale.items:
            item_data.append({
                'id': sale_item.item_id,
                'item_id': sale_item.item_id,
                'name': sale_item.item.item_name if sale_item.item else 'غير معروف',
                'price': float(sale_item.price),
                'quantity': float(sale_item.quantity),
                'total': float(sale_item.total)
            })

        result.append({
            'id': sale.id,
            'sale_number': sale.sale_number,
            'customer_id': sale.customer_id,
            'customerName': sale.customer.customer_name if sale.customer else 'عميل نقدي',
            'paymentMethod': sale.payment_method,
            'notes': sale.notes or '',
            'date': sale.created_at.strftime('%Y-%m-%d %H:%M:%S') if sale.created_at else '',
            'total': float(sale.total_amount),
            'items': item_data
        })

    return jsonify(result)

@app.route('/sales/held/<int:sale_id>', methods=['DELETE'])
@login_required
def delete_held_sale(sale_id):
    try:
        sale = Sale.query.get_or_404(sale_id)
        if sale.status != 'pending':
            return jsonify({'success': False, 'error': 'هذه الفاتورة ليست معلقة'}), 400
        db.session.delete(sale)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

# Reports
@app.route('/reports/sales')
@login_required
def sales_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    query = Sale.query

    if from_date:
        query = query.filter(Sale.created_at >= datetime.strptime(from_date, '%Y-%m-%d'))
    if to_date:
        query = query.filter(Sale.created_at <= datetime.strptime(to_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))

    sales_list = query.order_by(Sale.created_at.desc()).all()
    total = sum(sale.total_amount for sale in sales_list)
    items_list = Item.query.filter(Item.quantity > 0).all()
    customers_list = Customer.query.all()
    categories = {}
    for item in items_list:
        category = item.category if item.category else 'غير مصنف'
        categories.setdefault(category, []).append(item)

    return render_template('reports/sales_list.html', sales=sales_list, total=total,
                         from_date=from_date, to_date=to_date)

@app.route('/api/sale/<int:sale_id>')
@login_required
def get_sale_details(sale_id):
    try:
        sale = Sale.query.get_or_404(sale_id)

        items_data = []
        for sale_item in sale.items:
            items_data.append({
                'item_name': sale_item.item.item_name,
                'quantity': sale_item.quantity,
                'price': sale_item.price,
                'total': sale_item.total
            })

        sale_data = {
            'sale_number': sale.sale_number,
            'customer_name': sale.customer.customer_name if sale.customer else None,
            'user_name': sale.user.username,
            'total_amount': sale.total_amount,
            'payment_method': sale.payment_method,
            'paid_amount': sale.paid_amount,
            'remaining_amount': sale.remaining_amount,
            'status': sale.status,
            'notes': sale.notes,
            'created_at': sale.created_at.strftime('%Y-%m-%d %H:%M'),
            'items': items_data
        }

        return jsonify({'success': True, 'sale': sale_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/purchase/<int:purchase_id>')
@login_required
def get_purchase_details(purchase_id):
    try:
        purchase = Purchase.query.get_or_404(purchase_id)

        items_data = []
        for purchase_item in purchase.items:
            items_data.append({
                'item_name': purchase_item.item.item_name,
                'quantity': purchase_item.quantity,
                'price': purchase_item.price,
                'total': purchase_item.total
            })

        purchase_data = {
            'purchase_number': purchase.purchase_number,
            'supplier_name': purchase.supplier.supplier_name if purchase.supplier else None,
            'user_name': purchase.user.username,
            'total_amount': purchase.total_amount,
            'paid_amount': purchase.paid_amount,
            'remaining_amount': purchase.remaining_amount,
            'status': purchase.status,
            'notes': purchase.notes,
            'created_at': purchase.created_at.strftime('%Y-%m-%d %H:%M'),
            'items': items_data
        }

        return jsonify({'success': True, 'purchase': purchase_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/reports/customers')
@login_required
def customers_report():
    customers_list = Customer.query.all()
    total_balance = sum(customer.balance for customer in customers_list)
    return render_template('reports/customers.html', customers=customers_list,
                         total_balance=total_balance)

@app.route('/api/customer-details/<int:customer_id>')
@login_required
def get_customer_details(customer_id):
    try:
        customer = Customer.query.get_or_404(customer_id)

        sales_data = []
        for sale in customer.sales:
            sales_data.append({
                'sale_number': sale.sale_number,
                'created_at': sale.created_at.strftime('%Y-%m-%d %H:%M'),
                'total_amount': sale.total_amount,
                'paid_amount': sale.paid_amount,
                'remaining_amount': sale.remaining_amount,
                'status': sale.status
            })

        customer_data = {
            'customer_code': customer.customer_code,
            'customer_name': customer.customer_name,
            'address': customer.address,
            'phone': customer.phone,
            'balance': customer.balance,
            'sales_count': len(customer.sales),
            'total_sales': sum(sale.total_amount for sale in customer.sales),
            'sales': sales_data
        }

        return jsonify({'success': True, 'customer': customer_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/reports/purchases')
@login_required
def purchases_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    query = Purchase.query

    if from_date:
        query = query.filter(Purchase.created_at >= datetime.strptime(from_date, '%Y-%m-%d'))
    if to_date:
        query = query.filter(Purchase.created_at <= datetime.strptime(to_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))

    purchases_list = query.order_by(Purchase.created_at.desc()).all()
    total = sum(purchase.total_amount for purchase in purchases_list)
    items_list = Item.query.all()
    suppliers_list = Supplier.query.all()
    categories = {}
    for item in items_list:
        category = item.category if item.category else 'غير مصنف'
        categories.setdefault(category, []).append(item)

    return render_template('reports/purchases_list.html', purchases=purchases_list, total=total,
                         from_date=from_date, to_date=to_date)

@app.route('/reports/suppliers')
@login_required
def suppliers_report():
    suppliers_list = Supplier.query.all()
    total_balance = sum(supplier.balance for supplier in suppliers_list)
    return render_template('reports/suppliers.html', suppliers=suppliers_list,
                         total_balance=total_balance)

@app.route('/reports/expenses')
@login_required
def expenses_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    query = Expense.query

    if from_date:
        query = query.filter(Expense.expense_date >= from_date)
    if to_date:
        query = query.filter(Expense.expense_date <= to_date)

    expenses_list = query.order_by(Expense.expense_date.desc(), Expense.created_at.desc()).all()
    total = sum(expense.amount for expense in expenses_list)
    return render_template('reports/expenses.html', expenses=expenses_list, total=total,
                           from_date=from_date, to_date=to_date)

@app.route('/api/supplier-details/<int:supplier_id>')
@login_required
def get_supplier_details(supplier_id):
    try:
        supplier = Supplier.query.get_or_404(supplier_id)

        purchases_data = []
        for purchase in supplier.purchases:
            purchases_data.append({
                'purchase_number': purchase.purchase_number,
                'created_at': purchase.created_at.strftime('%Y-%m-%d %H:%M'),
                'total_amount': purchase.total_amount,
                'paid_amount': purchase.paid_amount,
                'remaining_amount': purchase.remaining_amount,
                'status': purchase.status
            })

        supplier_data = {
            'supplier_code': supplier.supplier_code,
            'supplier_name': supplier.supplier_name,
            'address': supplier.address,
            'phone': supplier.phone,
            'balance': supplier.balance,
            'purchases_count': len(supplier.purchases),
            'total_purchases': sum(purchase.total_amount for purchase in supplier.purchases),
            'purchases': purchases_data
        }

        return jsonify({'success': True, 'supplier': supplier_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/reports/customer-payments')
@login_required
def customer_payments_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    query = Payment.query

    if from_date:
        query = query.filter(Payment.created_at >= from_date)
    if to_date:
        query = query.filter(Payment.created_at <= to_date + ' 23:59:59')

    payments_list = query.order_by(Payment.created_at.desc()).all()
    total = sum(payment.amount for payment in payments_list)

    return render_template('reports/customer_payments_list.html', payments=payments_list, total=total,
                         from_date=from_date, to_date=to_date)

@app.route('/api/customer-payment/<int:payment_id>')
@login_required
def get_customer_payment_details(payment_id):
    try:
        payment = Payment.query.get_or_404(payment_id)

        payment_data = {
            'payment_number': payment.payment_number,
            'customer_name': payment.customer.customer_name,
            'customer_code': payment.customer.customer_code,
            'customer_balance': payment.customer.balance,
            'user_name': payment.user.username,
            'amount': payment.amount,
            'payment_method': payment.payment_method,
            'notes': payment.notes,
            'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M')
        }

        return jsonify({'success': True, 'payment': payment_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/reports/supplier-payments')
@login_required
def supplier_payments_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    query = SupplierPayment.query

    if from_date:
        query = query.filter(SupplierPayment.created_at >= from_date)
    if to_date:
        query = query.filter(SupplierPayment.created_at <= to_date + ' 23:59:59')

    payments_list = query.order_by(SupplierPayment.created_at.desc()).all()
    total = sum(payment.amount for payment in payments_list)

    return render_template('reports/supplier_payments_list.html', payments=payments_list, total=total,
                         from_date=from_date, to_date=to_date)

@app.route('/reports/salary-payments')
@login_required
def salary_payments_report():
    payment_month = request.args.get('payment_month')
    query = SalaryPayment.query

    if payment_month:
        query = query.filter(SalaryPayment.payment_month == payment_month)

    payments_list = query.order_by(
        SalaryPayment.payment_month.desc(), SalaryPayment.created_at.desc()
    ).all()
    total = sum(payment.amount for payment in payments_list)

    return render_template('reports/salary_payments_list.html', payments=payments_list,
                         total=total, payment_month=payment_month)

@app.route('/api/supplier-payment/<int:payment_id>')
@login_required
def get_supplier_payment_details(payment_id):
    try:
        payment = SupplierPayment.query.get_or_404(payment_id)

        payment_data = {
            'payment_number': payment.payment_number,
            'supplier_name': payment.supplier.supplier_name,
            'supplier_code': payment.supplier.supplier_code,
            'supplier_balance': payment.supplier.balance,
            'user_name': payment.user.username,
            'amount': payment.amount,
            'payment_method': payment.payment_method,
            'notes': payment.notes,
            'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M')
        }

        return jsonify({'success': True, 'payment': payment_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Users Management
@app.route('/users')
@login_required
@admin_required
def users():
    users_list = User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html', users=users_list)

@app.route('/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    try:
        user = User(
            username=request.form.get('username'),
            full_name=request.form.get('full_name'),
            role=request.form.get('role')
        )
        user.set_password(request.form.get('password'))
        db.session.add(user)
        db.session.commit()
        flash('تم إضافة المستخدم بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('users'))

@app.route('/users/toggle/<int:id>')
@login_required
@admin_required
def toggle_user(id):
    try:
        user = User.query.get_or_404(id)
        user.is_active = not user.is_active
        db.session.commit()
        flash('تم تحديث حالة المستخدم بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
    return redirect(url_for('users'))

def initialize_database():
    with app.app_context():
        try:
            db.create_all()
            if 'min_quantity' not in {column['name'] for column in inspect(db.engine).get_columns('items')}:
                try:
                    db.session.execute(text('ALTER TABLE items ADD COLUMN min_quantity FLOAT NOT NULL DEFAULT 5'))
                    db.session.commit()
                except Exception as migration_error:
                    db.session.rollback()
                    if 'duplicate column name' not in str(migration_error).lower():
                        raise
        except Exception as exc:
            if 'already exists' not in str(exc).lower():
                raise
            print('قاعدة البيانات موجودة مسبقاً، تم تجاوز إنشاء الجداول الحالية.')

        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', full_name='المدير', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('تم إنشاء مستخدم المدير: admin / admin123')

initialize_database()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

