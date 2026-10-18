from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from database import get_db, init_db
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'kisan_direct_market_secure_key_2026'

# Custom Jinja helper for format
@app.template_filter('currency')
def currency_filter(val):
    try:
        return f"₹{float(val):,.2f}"
    except (ValueError, TypeError):
        return f"₹{val}"

# Ensure database is initialized on startup
with app.app_context():
    init_db()

# -------------------------------------------------------------
# Decorators for Access Control
# -------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def farmer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in as a farmer to access the Farmer Portal.', 'warning')
            return redirect(url_for('login', next=request.url))
        if session.get('role') != 'farmer':
            flash('Access restricted to registered farmers only.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------------------------------------
# Context Processor for Global Navbar Stats
# -------------------------------------------------------------
@app.context_processor
def inject_global_data():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM crops WHERE available_qty > 0")
    total_active_crops = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE role = 'farmer'")
    total_farmers = c.fetchone()[0]
    conn.close()
    return {
        'total_active_crops': total_active_crops,
        'total_farmers': total_farmers,
        'now': datetime.now()
    }

# -------------------------------------------------------------
# Home Page
# -------------------------------------------------------------
@app.route('/')
def home():
    conn = get_db()
    c = conn.cursor()

    # Get featured fresh crops
    c.execute('''
        SELECT c.*, u.full_name as farmer_name, u.phone as farmer_phone,
               u.whatsapp as farmer_whatsapp, u.village, u.district, u.state, u.farm_name
        FROM crops c
        JOIN users u ON c.farmer_id = u.id
        WHERE c.available_qty > 0
        ORDER BY c.created_at DESC
        LIMIT 6
    ''')
    featured_crops = c.fetchall()

    # Get distinct categories
    c.execute("SELECT DISTINCT category FROM crops ORDER BY category ASC")
    categories = [r[0] for r in c.fetchall()]

    # Get recent Mandi vs Farmer price comparison (top 4)
    c.execute('''
        SELECT m.crop_name, m.modal_price, m.mandi_name, m.district,
               (SELECT MIN(c.price_per_unit) FROM crops c WHERE c.crop_name LIKE '%' || m.crop_name || '%') as farmer_min_price
        FROM mandi_prices m
        ORDER BY m.id ASC
        LIMIT 4
    ''')
    price_comparisons = c.fetchall()

    # Latest 2 farming tips
    c.execute("SELECT * FROM farming_tips ORDER BY id ASC LIMIT 2")
    tips = c.fetchall()

    conn.close()
    return render_template(
        'index.html',
        featured_crops=featured_crops,
        categories=categories,
        price_comparisons=price_comparisons,
        tips=tips
    )

# -------------------------------------------------------------
# Crops Catalog & Filter
# -------------------------------------------------------------
@app.route('/crops')
def crops_catalog():
    category = request.args.get('category', '').strip()
    search = request.args.get('q', '').strip()
    organic_only = request.args.get('organic', '').strip()
    sort = request.args.get('sort', 'newest').strip()

    conn = get_db()
    c = conn.cursor()

    query = '''
        SELECT c.*, u.full_name as farmer_name, u.phone as farmer_phone,
               u.whatsapp as farmer_whatsapp, u.village, u.district, u.state, u.farm_name
        FROM crops c
        JOIN users u ON c.farmer_id = u.id
        WHERE 1=1
    '''
    params = []

    if category:
        query += " AND c.category = ?"
        params.append(category)

    if search:
        query += ''' AND (
            c.crop_name LIKE ? OR c.variety LIKE ? OR c.description LIKE ?
            OR u.village LIKE ? OR u.district LIKE ? OR u.full_name LIKE ?
        )'''
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard, wildcard, wildcard, wildcard])

    if organic_only == '1':
        query += " AND c.organic = 1"

    if sort == 'price_asc':
        query += " ORDER BY c.price_per_unit ASC"
    elif sort == 'price_desc':
        query += " ORDER BY c.price_per_unit DESC"
    elif sort == 'qty_desc':
        query += " ORDER BY c.available_qty DESC"
    else:
        query += " ORDER BY c.created_at DESC"

    c.execute(query, params)
    crops = c.fetchall()

    # All categories for filter buttons
    c.execute("SELECT DISTINCT category FROM crops ORDER BY category ASC")
    categories = [r[0] for r in c.fetchall()]

    conn.close()
    return render_template(
        'crops.html',
        crops=crops,
        categories=categories,
        selected_category=category,
        search_query=search,
        organic_only=organic_only,
        selected_sort=sort
    )

# -------------------------------------------------------------
# Crop Detail Page
# -------------------------------------------------------------
@app.route('/crop/<int:crop_id>')
def crop_detail(crop_id):
    conn = get_db()
    c = conn.cursor()

    c.execute('''
        SELECT c.*, u.full_name as farmer_name, u.phone as farmer_phone,
               u.whatsapp as farmer_whatsapp, u.village, u.district, u.state,
               u.farm_name, u.bio as farmer_bio, u.email as farmer_email
        FROM crops c
        JOIN users u ON c.farmer_id = u.id
        WHERE c.id = ?
    ''', (crop_id,))
    crop = c.fetchone()

    if not crop:
        conn.close()
        flash('The requested crop listing was not found.', 'danger')
        return redirect(url_for('crops_catalog'))

    # Compare with Mandi price if available
    c.execute('''
        SELECT * FROM mandi_prices
        WHERE ? LIKE '%' || crop_name || '%' OR crop_name LIKE '%' || ? || '%'
        LIMIT 1
    ''', (crop['crop_name'], crop['crop_name']))
    mandi_benchmark = c.fetchone()

    # Other crops from this same farmer
    c.execute('''
        SELECT * FROM crops
        WHERE farmer_id = ? AND id != ?
        LIMIT 3
    ''', (crop['farmer_id'], crop_id))
    farmer_other_crops = c.fetchall()

    conn.close()
    return render_template(
        'crop_detail.html',
        crop=crop,
        mandi_benchmark=mandi_benchmark,
        farmer_other_crops=farmer_other_crops
    )

# -------------------------------------------------------------
# Direct Inquiry / Purchase Request (Connect consumer with farmer)
# -------------------------------------------------------------
@app.route('/inquire/<int:crop_id>', methods=['POST'])
def submit_inquiry(crop_id):
    consumer_name = request.form.get('consumer_name', '').strip()
    consumer_phone = request.form.get('consumer_phone', '').strip()
    consumer_email = request.form.get('consumer_email', '').strip()
    requested_qty_str = request.form.get('requested_qty', '0').strip()
    delivery_address = request.form.get('delivery_address', '').strip()
    message = request.form.get('message', '').strip()

    if not consumer_name or not consumer_phone:
        flash('Please provide your name and contact phone number.', 'danger')
        return redirect(url_for('crop_detail', crop_id=crop_id))

    try:
        requested_qty = float(requested_qty_str)
        if requested_qty <= 0:
            raise ValueError
    except ValueError:
        flash('Please enter a valid requested quantity.', 'danger')
        return redirect(url_for('crop_detail', crop_id=crop_id))

    conn = get_db()
    c = conn.cursor()

    c.execute('SELECT farmer_id, crop_name, available_qty, unit, price_per_unit FROM crops WHERE id = ?', (crop_id,))
    crop = c.fetchone()
    if not crop:
        conn.close()
        flash('Crop listing not found.', 'danger')
        return redirect(url_for('crops_catalog'))

    farmer_id = crop['farmer_id']
    consumer_id = session.get('user_id')

    c.execute('''
        INSERT INTO inquiries (
            crop_id, farmer_id, consumer_id, consumer_name, consumer_phone,
            consumer_email, requested_qty, delivery_address, message, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
    ''', (crop_id, farmer_id, consumer_id, consumer_name, consumer_phone, consumer_email, requested_qty, delivery_address, message))

    conn.commit()

    # Get farmer contact info to show direct WhatsApp & call link
    c.execute('SELECT full_name, phone, whatsapp FROM users WHERE id = ?', (farmer_id,))
    farmer = c.fetchone()
    conn.close()

    flash(f"Inquiry successfully submitted to farmer {farmer['full_name']}! You can also call or message them directly on WhatsApp below.", 'success')
    return redirect(url_for('crop_detail', crop_id=crop_id, inquiry_sent=1, farmer_phone=farmer['phone'], farmer_wa=farmer['whatsapp']))

# -------------------------------------------------------------
# Mandi Market Reference Prices
# -------------------------------------------------------------
@app.route('/mandi-prices')
def mandi_prices():
    search = request.args.get('q', '').strip()
    conn = get_db()
    c = conn.cursor()

    if search:
        c.execute('''
            SELECT * FROM mandi_prices
            WHERE crop_name LIKE ? OR mandi_name LIKE ? OR district LIKE ?
            ORDER BY crop_name ASC
        ''', (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        c.execute("SELECT * FROM mandi_prices ORDER BY crop_name ASC")

    prices = c.fetchall()
    conn.close()
    return render_template('mandi_prices.html', prices=prices, search_query=search)

# -------------------------------------------------------------
# Farmers Directory
# -------------------------------------------------------------
@app.route('/farmers')
def farmers_directory():
    conn = get_db()
    c = conn.cursor()

    c.execute('''
        SELECT u.*,
               COUNT(c.id) as crop_count,
               GROUP_CONCAT(c.crop_name, ', ') as crop_names
        FROM users u
        LEFT JOIN crops c ON u.id = c.farmer_id
        WHERE u.role = 'farmer'
        GROUP BY u.id
        ORDER BY u.full_name ASC
    ''')
    farmers = c.fetchall()
    conn.close()
    return render_template('farmers_directory.html', farmers=farmers)

# -------------------------------------------------------------
# Farming Tips & Guides
# -------------------------------------------------------------
@app.route('/tips')
def farming_tips():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM farming_tips ORDER BY id ASC")
    tips = c.fetchall()
    conn.close()
    return render_template('tips.html', tips=tips)

# -------------------------------------------------------------
# Authentication (Register, Login, Logout)
# -------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        whatsapp = request.form.get('whatsapp', '').strip() or phone
        village = request.form.get('village', '').strip()
        district = request.form.get('district', '').strip()
        state = request.form.get('state', '').strip()
        role = request.form.get('role', 'consumer').strip()
        farm_name = request.form.get('farm_name', '').strip()
        bio = request.form.get('bio', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validations
        if not full_name or not email or not phone or not village or not district or not state or not password:
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match. Please re-enter.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')

        conn = get_db()
        c = conn.cursor()

        # Check existing email
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
        if c.fetchone():
            conn.close()
            flash('An account with this email already exists. Please log in.', 'danger')
            return redirect(url_for('login'))

        pwd_hash = generate_password_hash(password)
        c.execute('''
            INSERT INTO users (
                full_name, email, phone, whatsapp, village, district, state,
                role, farm_name, bio, password_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (full_name, email, phone, whatsapp, village, district, state, role, farm_name, bio, pwd_hash))

        conn.commit()
        user_id = c.lastrowid
        conn.close()

        # Auto login
        session['user_id'] = user_id
        session['full_name'] = full_name
        session['role'] = role
        session['email'] = email

        flash(f'Welcome, {full_name}! Your account has been created.', 'success')
        if role == 'farmer':
            return redirect(url_for('farmer_dashboard'))
        else:
            return redirect(url_for('buyer_dashboard'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('login.html')

        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            session['email'] = user['email']

            flash(f"Welcome back, {user['full_name']}!", 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)

            if user['role'] == 'farmer':
                return redirect(url_for('farmer_dashboard'))
            else:
                return redirect(url_for('buyer_dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))

# -------------------------------------------------------------
# Farmer Portal
# -------------------------------------------------------------
@app.route('/farmer/dashboard')
@farmer_required
def farmer_dashboard():
    farmer_id = session['user_id']
    conn = get_db()
    c = conn.cursor()

    # Get farmer's crop listings
    c.execute('''
        SELECT * FROM crops
        WHERE farmer_id = ?
        ORDER BY created_at DESC
    ''', (farmer_id,))
    my_crops = c.fetchall()

    # Get inquiries received
    c.execute('''
        SELECT i.*, c.crop_name, c.unit, c.price_per_unit
        FROM inquiries i
        JOIN crops c ON i.crop_id = c.id
        WHERE i.farmer_id = ?
        ORDER BY i.created_at DESC
    ''', (farmer_id,))
    inquiries = c.fetchall()

    # Stats
    total_listings = len(my_crops)
    active_stock_items = sum(1 for crop in my_crops if crop['available_qty'] > 0)
    pending_inquiries = sum(1 for inq in inquiries if inq['status'] == 'Pending')

    conn.close()
    return render_template(
        'farmer_dashboard.html',
        my_crops=my_crops,
        inquiries=inquiries,
        total_listings=total_listings,
        active_stock_items=active_stock_items,
        pending_inquiries=pending_inquiries
    )

@app.route('/farmer/add-crop', methods=['GET', 'POST'])
@farmer_required
def add_crop():
    if request.method == 'POST':
        farmer_id = session['user_id']
        crop_name = request.form.get('crop_name', '').strip()
        category = request.form.get('category', '').strip()
        variety = request.form.get('variety', '').strip()
        price_per_unit = float(request.form.get('price_per_unit', 0))
        unit = request.form.get('unit', 'kg').strip()
        min_order_qty = float(request.form.get('min_order_qty', 1))
        available_qty = float(request.form.get('available_qty', 0))
        harvest_date = request.form.get('harvest_date', '').strip()
        status = request.form.get('status', 'Available Now').strip()
        description = request.form.get('description', '').strip()
        organic = 1 if request.form.get('organic') == '1' else 0
        delivery_available = 1 if request.form.get('delivery_available') == '1' else 0
        pickup_location = request.form.get('pickup_location', '').strip()
        image_emoji = request.form.get('image_emoji', '🌾').strip()

        if not crop_name or not category or price_per_unit <= 0 or available_qty < 0:
            flash('Please fill in all mandatory crop details accurately.', 'danger')
            return render_template('crop_form.html', action='add')

        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO crops (
                farmer_id, crop_name, category, variety, price_per_unit, unit,
                min_order_qty, available_qty, harvest_date, status, description,
                organic, delivery_available, pickup_location, image_emoji
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            farmer_id, crop_name, category, variety, price_per_unit, unit,
            min_order_qty, available_qty, harvest_date, status, description,
            organic, delivery_available, pickup_location, image_emoji
        ))
        conn.commit()
        conn.close()

        flash(f'Crop listing "{crop_name}" added successfully and is now visible to consumers!', 'success')
        return redirect(url_for('farmer_dashboard'))

    return render_template('crop_form.html', action='add', crop=None)

@app.route('/farmer/edit-crop/<int:crop_id>', methods=['GET', 'POST'])
@farmer_required
def edit_crop(crop_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM crops WHERE id = ? AND farmer_id = ?', (crop_id, session['user_id']))
    crop = c.fetchone()

    if not crop:
        conn.close()
        flash('Crop listing not found or you do not have permission to edit it.', 'danger')
        return redirect(url_for('farmer_dashboard'))

    if request.method == 'POST':
        crop_name = request.form.get('crop_name', '').strip()
        category = request.form.get('category', '').strip()
        variety = request.form.get('variety', '').strip()
        price_per_unit = float(request.form.get('price_per_unit', 0))
        unit = request.form.get('unit', 'kg').strip()
        min_order_qty = float(request.form.get('min_order_qty', 1))
        available_qty = float(request.form.get('available_qty', 0))
        harvest_date = request.form.get('harvest_date', '').strip()
        status = request.form.get('status', 'Available Now').strip()
        description = request.form.get('description', '').strip()
        organic = 1 if request.form.get('organic') == '1' else 0
        delivery_available = 1 if request.form.get('delivery_available') == '1' else 0
        pickup_location = request.form.get('pickup_location', '').strip()
        image_emoji = request.form.get('image_emoji', '🌾').strip()

        c.execute('''
            UPDATE crops SET
                crop_name = ?, category = ?, variety = ?, price_per_unit = ?, unit = ?,
                min_order_qty = ?, available_qty = ?, harvest_date = ?, status = ?,
                description = ?, organic = ?, delivery_available = ?, pickup_location = ?,
                image_emoji = ?
            WHERE id = ? AND farmer_id = ?
        ''', (
            crop_name, category, variety, price_per_unit, unit,
            min_order_qty, available_qty, harvest_date, status, description,
            organic, delivery_available, pickup_location, image_emoji,
            crop_id, session['user_id']
        ))
        conn.commit()
        conn.close()

        flash(f'Crop listing "{crop_name}" updated successfully.', 'success')
        return redirect(url_for('farmer_dashboard'))

    conn.close()
    return render_template('crop_form.html', action='edit', crop=crop)

@app.route('/farmer/delete-crop/<int:crop_id>', methods=['POST'])
@farmer_required
def delete_crop(crop_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM crops WHERE id = ? AND farmer_id = ?', (crop_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Crop listing removed.', 'info')
    return redirect(url_for('farmer_dashboard'))

@app.route('/farmer/inquiry/<int:inquiry_id>/status', methods=['POST'])
@farmer_required
def update_inquiry_status(inquiry_id):
    new_status = request.form.get('status', 'Pending').strip()
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE inquiries SET status = ?
        WHERE id = ? AND farmer_id = ?
    ''', (new_status, inquiry_id, session['user_id']))
    conn.commit()
    conn.close()
    flash(f'Inquiry status updated to {new_status}.', 'success')
    return redirect(url_for('farmer_dashboard'))

# -------------------------------------------------------------
# Consumer / Buyer Dashboard
# -------------------------------------------------------------
@app.route('/buyer/dashboard')
@login_required
def buyer_dashboard():
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()

    # Inquiries submitted by this consumer
    c.execute('''
        SELECT i.*, c.crop_name, c.unit, c.price_per_unit, c.image_emoji,
               u.full_name as farmer_name, u.phone as farmer_phone,
               u.whatsapp as farmer_whatsapp, u.village, u.district
        FROM inquiries i
        JOIN crops c ON i.crop_id = c.id
        JOIN users u ON i.farmer_id = u.id
        WHERE i.consumer_id = ?
        ORDER BY i.created_at DESC
    ''', (user_id,))
    my_inquiries = c.fetchall()

    conn.close()
    return render_template('buyer_dashboard.html', my_inquiries=my_inquiries)

# -------------------------------------------------------------
# JSON API for Instant Search & Price Calculation
# -------------------------------------------------------------
@app.route('/api/crops')
def api_crops():
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    conn = get_db()
    c = conn.cursor()
    query = '''
        SELECT c.id, c.crop_name, c.category, c.variety, c.price_per_unit, c.unit,
               c.available_qty, c.organic, c.image_emoji, c.status,
               u.full_name as farmer_name, u.phone as farmer_phone,
               u.village, u.district, u.state
        FROM crops c
        JOIN users u ON c.farmer_id = u.id
        WHERE c.available_qty > 0
    '''
    params = []
    if category:
        query += " AND c.category = ?"
        params.append(category)
    if search:
        query += " AND (c.crop_name LIKE ? OR u.village LIKE ? OR u.district LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " ORDER BY c.created_at DESC"
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

if __name__ == '__main__':
    # Run the application
    app.run(debug=True, port=5000, host='127.0.0.1')
