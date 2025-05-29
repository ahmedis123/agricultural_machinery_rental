import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

# إنشاء تطبيق Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'agricultural_machinery_rental_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

# التأكد من وجود مجلد التحميلات
os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']), exist_ok=True)

# الاتصال بقاعدة البيانات
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('database.db')
        g.db.row_factory = sqlite3.Row
    return g.db

# إغلاق الاتصال بقاعدة البيانات
@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# إنشاء جداول قاعدة البيانات
def init_db():
    db = get_db()
    
    # إنشاء جدول المشرفين
    db.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    
    # إنشاء جدول الولايات
    db.execute('''
    CREATE TABLE IF NOT EXISTS states (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')
    
    # إنشاء جدول المحليات
    db.execute('''
    CREATE TABLE IF NOT EXISTS localities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        state_id INTEGER NOT NULL,
        FOREIGN KEY (state_id) REFERENCES states (id),
        UNIQUE(name, state_id)
    )
    ''')
    
    # إنشاء جدول أنواع الآلات
    db.execute('''
    CREATE TABLE IF NOT EXISTS machine_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')
    
    # إنشاء جدول الآلات الزراعية
    db.execute('''
    CREATE TABLE IF NOT EXISTS machines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type_id INTEGER NOT NULL,
        state_id INTEGER NOT NULL,
        locality_id INTEGER NOT NULL,
        description TEXT,
        image TEXT,
        owner_phone TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (type_id) REFERENCES machine_types (id),
        FOREIGN KEY (state_id) REFERENCES states (id),
        FOREIGN KEY (locality_id) REFERENCES localities (id)
    )
    ''')
    
    # إنشاء جدول طلبات الحجز
    db.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        machine_id INTEGER NOT NULL,
        acres INTEGER NOT NULL,
        crop_type TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (machine_id) REFERENCES machines (id)
    )
    ''')
    
    # إدخال بيانات المشرف الافتراضي
    admin_exists = db.execute('SELECT id FROM admins WHERE username = ?', ('admin',)).fetchone()
    if not admin_exists:
        db.execute('INSERT INTO admins (username, password) VALUES (?, ?)',
                  ('admin', generate_password_hash('admin123')))
    
    # إدخال بيانات الولايات السودانية
    states = [
        'الخرطوم', 'الجزيرة', 'البحر الأحمر', 'كسلا', 'القضارف', 'سنار', 'النيل الأبيض', 'النيل الأزرق',
        'الشمالية', 'نهر النيل', 'شمال كردفان', 'جنوب كردفان', 'غرب كردفان', 'شمال دارفور',
        'جنوب دارفور', 'شرق دارفور', 'غرب دارفور', 'وسط دارفور'
    ]
    
    for state in states:
        state_exists = db.execute('SELECT id FROM states WHERE name = ?', (state,)).fetchone()
        if not state_exists:
            db.execute('INSERT INTO states (name) VALUES (?)', (state,))
    
    # إدخال بيانات المحليات (أمثلة لبعض المحليات)
    localities = [
    # الخرطوم (1)
    ('الخرطوم', 1), ('جبل أولياء', 1), ('بحري', 1), ('شرق النيل', 1), ('أمدرمان', 1), ('كرري', 1), ('أم بدة', 1),
    # الجزيرة (2)
    ('ود مدني', 2), ('الحصاحيصا', 2), ('الكاملين', 2), ('المناقل', 2), ('جنوب الجزيرة', 2), ('شرق الجزيرة', 2), ('أم القرى', 2), ('مدني الكبرى', 2),

    # البحر الأحمر (3)
    ('بورتسودان', 3), ('سواكن', 3), ('سنكات', 3), ('هيا', 3), ('عقيق', 3), ('طوكر', 3), ('دربات', 3),

    # كسلا (4)
    ('كسلا', 4), ('حلفا الجديدة', 4), ('ريفي كسلا', 4), ('تلكوك', 4), ('ود الحليو', 4), ('أروما', 4), ('نهر عطبرة', 4),

    # القضارف (5)
    ('القضارف', 5), ('الفاو', 5), ('القلابات الشرقية', 5), ('القلابات الغربية', 5), ('رهد القضارف', 5), ('باسندة', 5), ('البطانة', 5),

    # سنار (6)
    ('سنجة', 6), ('سنار', 6), ('الدالي والمزموم', 6), ('السوكي', 6), ('أبو حجار', 6),

    # النيل الأزرق (7)
    ('الدمازين', 7), ('الروصيرص', 7), ('باو', 7), ('الكرمك', 7), ('ود الماحي', 7),

    # النيل الأبيض (8)
    ('كوستي', 8), ('ربك', 8), ('تندلتي', 8), ('السلام', 8), ('الجبلين', 8), ('قلي', 8), ('الدويم', 8), ('أم رمتة', 8),

    # شمال كردفان (9)
    ('الأبيض', 9), ('شيكان', 9), ('بارا', 9), ('أم روابة', 9), ('الرهد', 9), ('سودري', 9), ('النهود', 9),

    # جنوب كردفان (10)
    ('كادقلي', 10), ('الدلنج', 10), ('أبو جبيهة', 10), ('العباسية', 10), ('تلودي', 10), ('الريفي الشرقي', 10),

    # غرب كردفان (11)
    ('الفولة', 11), ('النهود', 11), ('أبوزبد', 11), ('الخور أبو حبل', 11), ('غبيش', 11), ('بليلة', 11), ('المجلد', 11),

    # شمال دارفور (12)
    ('الفاشر', 12), ('الكومة', 12), ('المالحة', 12), ('كتم', 12), ('كبكابية', 12), ('الطويشة', 12), ('أم كدادة', 12),

    # جنوب دارفور (13)
    ('نيالا', 13), ('عد الفرسان', 13), ('رهيد البردي', 13), ('برام', 13), ('السلام', 13), ('شرق جبل مرة', 13), ('تلس', 13),

    # وسط دارفور (14)
    ('زالنجي', 14), ('نيرتتي', 14), ('وادي صالح', 14), ('أم دخن', 14), ('روكرو', 14), ('غرب جبل مرة', 14),

    # شرق دارفور (15)
    ('الضعين', 15), ('أبو كارنكا', 15), ('يس', 15), ('شعيرية', 15), ('الفردوس', 15), ('أبو جابرة', 15), ('عديلة', 15),

    # غرب دارفور (16)
    ('الجنينة', 16), ('كرينك', 16), ('سربا', 16), ('بيضة', 16), ('أبو زيبد', 16), ('هابل', 16), ('مورني', 16)
    ]
    
    for name, state_id in localities:
        locality_exists = db.execute('SELECT id FROM localities WHERE name = ? AND state_id = ?', (name, state_id)).fetchone()
        if not locality_exists:
            db.execute('INSERT INTO localities (name, state_id) VALUES (?, ?)', (name, state_id))
    
    # إدخال بيانات أنواع الآلات الزراعية
    machine_types = [
    'جرار',
    'آلة حرث',
    'آلة بذر',
    'دراّسة',
    'حصادة',
    'مضخة ري',
    'آلة رش مبيدات',
    'عربة نقل'
    ]
    
    for machine_type in machine_types:
        type_exists = db.execute('SELECT id FROM machine_types WHERE name = ?', (machine_type,)).fetchone()
        if not type_exists:
            db.execute('INSERT INTO machine_types (name) VALUES (?)', (machine_type,))
    
    db.commit()

# تهيئة قاعدة البيانات عند بدء التطبيق
with app.app_context():
    init_db()

# التحقق من حالة تسجيل الدخول
def is_logged_in():
    return 'user_id' in session

# صفحة الرئيسية
@app.route('/')
def index():
    db = get_db()
    machines = db.execute('''
        SELECT m.id, m.name, mt.name as type, s.name as state, l.name as locality, 
               m.description, m.image, m.owner_phone
        FROM machines m
        JOIN machine_types mt ON m.type_id = mt.id
        JOIN states s ON m.state_id = s.id
        JOIN localities l ON m.locality_id = l.id
        ORDER BY m.created_at DESC
        LIMIT 6
    ''').fetchall()
    
    states = db.execute('SELECT * FROM states ORDER BY name').fetchall()
    
    return render_template('index.html', machines=machines, states=states)

# صفحة عرض الآلات الزراعية مع الفلترة
@app.route('/machines')
def machines():
    db = get_db()
    
    state_id = request.args.get('state_id', type=int)
    locality_id = request.args.get('locality_id', type=int)
    
    query = '''
        SELECT m.id, m.name, mt.name as type, s.name as state, l.name as locality, 
               m.description, m.image, m.owner_phone
        FROM machines m
        JOIN machine_types mt ON m.type_id = mt.id
        JOIN states s ON m.state_id = s.id
        JOIN localities l ON m.locality_id = l.id
        WHERE 1=1
    '''
    params = []
    
    if state_id:
        query += ' AND m.state_id = ?'
        params.append(state_id)
    
    if locality_id:
        query += ' AND m.locality_id = ?'
        params.append(locality_id)
    
    query += ' ORDER BY m.created_at DESC'
    
    machines = db.execute(query, params).fetchall()
    states = db.execute('SELECT * FROM states ORDER BY name').fetchall()
    
    localities = []
    if state_id:
        localities = db.execute('SELECT * FROM localities WHERE state_id = ? ORDER BY name', (state_id,)).fetchall()
    
    return render_template('machines.html', machines=machines, states=states, localities=localities, 
                           selected_state=state_id, selected_locality=locality_id)

# الحصول على المحليات حسب الولاية (AJAX)
@app.route('/get_localities/<int:state_id>')
def get_localities(state_id):
    db = get_db()
    localities = db.execute('SELECT * FROM localities WHERE state_id = ? ORDER BY name', (state_id,)).fetchall()
    localities_list = [{'id': l['id'], 'name': l['name']} for l in localities]
    return {'localities': localities_list}

# صفحة تفاصيل الآلة وطلب الحجز
@app.route('/machine/<int:machine_id>', methods=['GET', 'POST'])
def machine_details(machine_id):
    db = get_db()
    
    machine = db.execute('''
        SELECT m.id, m.name, mt.name as type, mt.id as type_id, s.name as state, l.name as locality, 
               m.description, m.image, m.owner_phone
        FROM machines m
        JOIN machine_types mt ON m.type_id = mt.id
        JOIN states s ON m.state_id = s.id
        JOIN localities l ON m.locality_id = l.id
        WHERE m.id = ?
    ''', (machine_id,)).fetchone()
    
    if not machine:
        flash('الآلة غير موجودة', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        acres = request.form.get('acres')
        crop_type = request.form.get('crop_type')
        notes = request.form.get('notes')
        
        if not name or not phone or not acres:
            flash('يرجى ملء جميع الحقول المطلوبة', 'error')
        else:
            db.execute('''
                INSERT INTO bookings (name, phone, machine_id, acres, crop_type, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, phone, machine_id, acres, crop_type, notes))
            db.commit()
            flash('تم إرسال طلب الحجز بنجاح. يرجى الاتصال بمالك الآلة لتأكيد الحجز.', 'success')
            return redirect(url_for('machine_details', machine_id=machine_id))
    
    return render_template('machine_details.html', machine=machine)

# صفحة تسجيل دخول المشرف
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if is_logged_in():
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db()
        admin = db.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
        
        if admin and check_password_hash(admin['password'], password):
            session['user_id'] = admin['id']
            session['username'] = admin['username']
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('admin/login.html')

# تسجيل خروج المشرف
@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('index'))

# لوحة تحكم المشرف
@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_logged_in():
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('admin_login'))
    
    db = get_db()
    machines_count = db.execute('SELECT COUNT(*) as count FROM machines').fetchone()['count']
    bookings_count = db.execute('SELECT COUNT(*) as count FROM bookings').fetchone()['count']
    
    return render_template('admin/dashboard.html', machines_count=machines_count, bookings_count=bookings_count)

# إدارة الآلات الزراعية
@app.route('/admin/machines')
def admin_machines():
    if not is_logged_in():
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('admin_login'))
    
    db = get_db()
    machines = db.execute('''
        SELECT m.id, m.name, mt.name as type, s.name as state, l.name as locality, 
               m.description, m.image, m.owner_phone
        FROM machines m
        JOIN machine_types mt ON m.type_id = mt.id
        JOIN states s ON m.state_id = s.id
        JOIN localities l ON m.locality_id = l.id
        ORDER BY m.created_at DESC
    ''').fetchall()
    
    return render_template('admin/machines.html', machines=machines)

# إضافة آلة زراعية جديدة
@app.route('/admin/machines/add', methods=['GET', 'POST'])
def add_machine():
    if not is_logged_in():
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('admin_login'))
    
    db = get_db()
    states = db.execute('SELECT * FROM states ORDER BY name').fetchall()
    machine_types = db.execute('SELECT * FROM machine_types ORDER BY name').fetchall()
    
    if request.method == 'POST':
        name = request.form.get('name')
        type_id = request.form.get('type_id')
        state_id = request.form.get('state_id')
        locality_id = request.form.get('locality_id')
        description = request.form.get('description')
        owner_phone = request.form.get('owner_phone')
        
        # التحقق من الحقول المطلوبة
        if not name or not type_id or not state_id or not locality_id or not owner_phone:
            flash('يرجى ملء جميع الحقول المطلوبة', 'error')
            localities = []
            if state_id:
                localities = db.execute('SELECT * FROM localities WHERE state_id = ? ORDER BY name', (state_id,)).fetchall()
            return render_template('admin/add_machine.html', states=states, machine_types=machine_types, 
                                  localities=localities, form=request.form)
        
        # معالجة الصورة
        image_filename = None
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                filename = secure_filename(image.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                image_filename = f"{timestamp}_{filename}"
                image.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], image_filename))
        
        # إضافة الآلة إلى قاعدة البيانات
        db.execute('''
            INSERT INTO machines (name, type_id, state_id, locality_id, description, image, owner_phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, type_id, state_id, locality_id, description, image_filename, owner_phone))
        db.commit()
        
        flash('تمت إضافة الآلة بنجاح', 'success')
        return redirect(url_for('admin_machines'))
    
    return render_template('admin/add_machine.html', states=states, machine_types=machine_types, localities=[])

# تعديل آلة زراعية
@app.route('/admin/machines/edit/<int:machine_id>', methods=['GET', 'POST'])
def edit_machine(machine_id):
    if not is_logged_in():
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('admin_login'))
    
    db = get_db()
    machine = db.execute('''
        SELECT * FROM machines WHERE id = ?
    ''', (machine_id,)).fetchone()
    
    if not machine:
        flash('الآلة غير موجودة', 'error')
        return redirect(url_for('admin_machines'))
    
    states = db.execute('SELECT * FROM states ORDER BY name').fetchall()
    machine_types = db.execute('SELECT * FROM machine_types ORDER BY name').fetchall()
    localities = db.execute('SELECT * FROM localities WHERE state_id = ? ORDER BY name', (machine['state_id'],)).fetchall()
    
    if request.method == 'POST':
        name = request.form.get('name')
        type_id = request.form.get('type_id')
        state_id = request.form.get('state_id')
        locality_id = request.form.get('locality_id')
        description = request.form.get('description')
        owner_phone = request.form.get('owner_phone')
        
        # التحقق من الحقول المطلوبة
        if not name or not type_id or not state_id or not locality_id or not owner_phone:
            flash('يرجى ملء جميع الحقول المطلوبة', 'error')
            localities = db.execute('SELECT * FROM localities WHERE state_id = ? ORDER BY name', (state_id,)).fetchall()
            return render_template('admin/edit_machine.html', machine=machine, states=states, 
                                  machine_types=machine_types, localities=localities, form=request.form)
        
        # معالجة الصورة
        image_filename = machine['image']
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                # حذف الصورة القديمة إذا وجدت
                if machine['image']:
                    old_image_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], machine['image'])
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                filename = secure_filename(image.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                image_filename = f"{timestamp}_{filename}"
                image.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], image_filename))
        
        # تحديث الآلة في قاعدة البيانات
        db.execute('''
            UPDATE machines
            SET name = ?, type_id = ?, state_id = ?, locality_id = ?, description = ?, image = ?, owner_phone = ?
            WHERE id = ?
        ''', (name, type_id, state_id, locality_id, description, image_filename, owner_phone, machine_id))
        db.commit()
        
        flash('تم تحديث الآلة بنجاح', 'success')
        return redirect(url_for('admin_machines'))
    
    return render_template('admin/edit_machine.html', machine=machine, states=states, 
                          machine_types=machine_types, localities=localities)

# حذف آلة زراعية
@app.route('/admin/machines/delete/<int:machine_id>', methods=['POST'])
def delete_machine(machine_id):
    if not is_logged_in():
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('admin_login'))
    
    db = get_db()
    machine = db.execute('SELECT * FROM machines WHERE id = ?', (machine_id,)).fetchone()
    
    if machine:
        # حذف الصورة إذا وجدت
        if machine['image']:
            image_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], machine['image'])
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # حذف طلبات الحجز المرتبطة بالآلة
        db.execute('DELETE FROM bookings WHERE machine_id = ?', (machine_id,))
        
        # حذف الآلة
        db.execute('DELETE FROM machines WHERE id = ?', (machine_id,))
        db.commit()
        
        flash('تم حذف الآلة بنجاح', 'success')
    else:
        flash('الآلة غير موجودة', 'error')
    
    return redirect(url_for('admin_machines'))

# إدارة طلبات الحجز
@app.route('/admin/bookings')
def admin_bookings():
    if not is_logged_in():
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('admin_login'))
    
    db = get_db()
    bookings = db.execute('''
        SELECT b.id, b.name, b.phone, b.acres, b.crop_type, b.notes, b.created_at,
               m.name as machine_name, m.owner_phone
        FROM bookings b
        JOIN machines m ON b.machine_id = m.id
        ORDER BY b.created_at DESC
    ''').fetchall()
    
    return render_template('admin/bookings.html', bookings=bookings)

# حذف طلب حجز
@app.route('/admin/bookings/delete/<int:booking_id>', methods=['POST'])
def delete_booking(booking_id):
    if not is_logged_in():
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('admin_login'))
    
    db = get_db()
    db.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
    db.commit()
    
    flash('تم حذف طلب الحجز بنجاح', 'success')
    return redirect(url_for('admin_bookings'))

# تشغيل التطبيق
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
