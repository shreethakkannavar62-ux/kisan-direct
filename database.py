import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime, date

DATABASE = 'farmer_market.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users table (Farmers & Consumers)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            whatsapp TEXT,
            village TEXT NOT NULL,
            district TEXT NOT NULL,
            state TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'consumer',
            farm_name TEXT,
            bio TEXT,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Crops table (Listings posted by farmers)
    c.execute('''
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            crop_name TEXT NOT NULL,
            category TEXT NOT NULL,
            variety TEXT,
            price_per_unit REAL NOT NULL,
            unit TEXT NOT NULL DEFAULT 'kg',
            min_order_qty REAL NOT NULL DEFAULT 1,
            available_qty REAL NOT NULL,
            harvest_date TEXT,
            status TEXT NOT NULL DEFAULT 'Available Now',
            description TEXT,
            organic INTEGER NOT NULL DEFAULT 0,
            delivery_available INTEGER NOT NULL DEFAULT 1,
            pickup_location TEXT,
            image_emoji TEXT DEFAULT '🌾',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Inquiries / Orders table (Direct contact from consumers to farmers)
    c.execute('''
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_id INTEGER NOT NULL,
            farmer_id INTEGER NOT NULL,
            consumer_id INTEGER,
            consumer_name TEXT NOT NULL,
            consumer_phone TEXT NOT NULL,
            consumer_email TEXT,
            requested_qty REAL NOT NULL,
            delivery_address TEXT,
            message TEXT,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (crop_id) REFERENCES crops(id) ON DELETE CASCADE,
            FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (consumer_id) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')

    # Mandi / Market Reference Prices
    c.execute('''
        CREATE TABLE IF NOT EXISTS mandi_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT NOT NULL,
            category TEXT NOT NULL,
            mandi_name TEXT NOT NULL,
            district TEXT NOT NULL,
            modal_price REAL NOT NULL,
            min_price REAL NOT NULL,
            max_price REAL NOT NULL,
            unit TEXT NOT NULL DEFAULT 'kg',
            date_reported TEXT NOT NULL
        )
    ''')

    # Farming tips and best practices
    c.execute('''
        CREATE TABLE IF NOT EXISTS farming_tips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            read_time TEXT DEFAULT '3 min',
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()

    # Seed initial data if users table is empty
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    c = conn.cursor()
    pwd_hash = generate_password_hash('farmer123')

    # 1. Farmers
    farmers = [
        (
            'Ramesh Bhai Patel', 'ramesh@kisan.in', '9825123456', '9825123456',
            'Boriavi', 'Anand', 'Gujarat', 'farmer', 'Patel Organic Farms',
            '3rd generation farmer cultivating chemical-free vegetables and pulses with solar-powered drip irrigation.',
            pwd_hash
        ),
        (
            'Sunita Tai Shinde', 'sunita@kisan.in', '9422987654', '9422987654',
            'Pimpalgaon', 'Nashik', 'Maharashtra', 'farmer', 'Shinde Agro Orchards',
            'Specializing in premium table grapes, red onions, and fresh seasonal tomatoes. Direct farm pickup available.',
            pwd_hash
        ),
        (
            'Balwinder Singh', 'balwinder@kisan.in', '9876501234', '9876501234',
            'Samrala', 'Ludhiana', 'Punjab', 'farmer', 'Green Earth Bio Farms',
            'Certified 100% organic producer of traditional Sharbati wheat, Basmati paddy, and seasonal mustard greens.',
            pwd_hash
        )
    ]

    c.executemany('''
        INSERT INTO users (full_name, email, phone, whatsapp, village, district, state, role, farm_name, bio, password_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', farmers)

    # 2. Sample Consumer
    consumer_pwd = generate_password_hash('buyer123')
    c.execute('''
        INSERT INTO users (full_name, email, phone, whatsapp, village, district, state, role, bio, password_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Priya Sharma', 'priya@consumer.com', '9819001122', '9819001122',
        'Bandra West', 'Mumbai Suburban', 'Maharashtra', 'consumer',
        'Looking for direct bulk purchases of farm-fresh organic produce for family and housing society.',
        consumer_pwd
    ))

    # 3. Crops
    crops = [
        (
            1, 'Farm Fresh Organic Tomatoes', 'Vegetables', 'Desi Hybrid (Plump & Juicy)',
            28.00, 'kg', 5.0, 450.0, '2026-10-16', 'Available Now',
            'Naturally sun-ripened tomatoes grown without chemical pesticides. Rich in flavor, ideal for purées, curries, and salads.',
            1, 1, 'Boriavi Farm Gate No. 2, Anand-Nadiad Highway', '🍅'
        ),
        (
            1, 'Green Bell Peppers (Capsicum)', 'Vegetables', 'Green Bell / Shimla Mirch',
            45.00, 'kg', 2.0, 200.0, '2026-10-17', 'Available Now',
            'Crisp, crunchy polyhouse capsicums harvested early morning. Retains freshness for over a week under refrigeration.',
            1, 1, 'Boriavi Farm Gate No. 2', '🫑'
        ),
        (
            1, 'Sweet Yellow Corn (Maize)', 'Vegetables', 'Sugar 75 Hybrid',
            22.00, 'kg', 10.0, 800.0, '2026-10-18', 'Available Now',
            'Sweet, tender golden cobs freshly plucked. Great for boiling, grilling, or corn snacks.',
            0, 1, 'Patel Farm Hub, Anand', '🌽'
        ),
        (
            2, 'Nashik Red Onions (Medium-Large)', 'Vegetables', 'Garwa Late Kharif',
            26.00, 'kg', 10.0, 1500.0, '2026-10-14', 'Available Now',
            'World famous Nashik red pungent onions with long shelf life. Cured naturally in ventilated sheds.',
            0, 1, 'Pimpalgaon Baswant APMC Bypass Shed', '🧅'
        ),
        (
            2, 'Seedless Black Grapes (Sharad Seedless)', 'Fruits', 'Sharad Seedless Export Grade',
            85.00, 'kg', 5.0, 600.0, '2026-10-15', 'Available Now',
            'Crisp, sweet berries with brix reading > 18. Carefully hand-trimmed bunches ready for direct consumption.',
            1, 1, 'Shinde Agro Orchards Cold Storage, Nashik', '🍇'
        ),
        (
            2, 'Fresh Pomegranates (Bhagwa Variety)', 'Fruits', 'Bhagwa Grade A',
            110.00, 'kg', 5.0, 350.0, '2026-10-12', 'Available Now',
            'Deep red arils, sweet and soft-seeded. High medicinal and antioxidant values, direct from orchard.',
            1, 1, 'Shinde Agro Orchards, Nashik', '🍎'
        ),
        (
            3, 'Sharbati Whole Wheat Grain', 'Grains & Pulses', 'Traditional Sharbati Sehore',
            42.00, 'kg', 25.0, 3200.0, '2026-09-28', 'Available Now',
            'Golden bold grains yielding soft and sweet rotis. Machine cleaned, moisture tested at 11%, zero stone guarantee.',
            1, 1, 'Green Earth Store, Samrala Road, Ludhiana', '🌾'
        ),
        (
            3, 'Aromatic Traditional Basmati Rice (Paddy/Milled)', 'Grains & Pulses', 'Traditional Basmati 1121 Extra Long',
            95.00, 'kg', 10.0, 1800.0, '2026-09-20', 'Available Now',
            'Aged 12 months for fluffiness and elongation upon cooking. Premium aroma that fills the entire kitchen.',
            0, 1, 'Green Earth Store, Ludhiana', '🍚'
        ),
        (
            3, 'Organic Yellow Mustard Seeds (Sarson)', 'Spices & Herbs', 'Pusa Bold',
            80.00, 'kg', 5.0, 400.0, '2026-10-05', 'Available Now',
            'High oil content yellow mustard seeds. Cleaned and sun-dried, perfect for cold-pressed oil extraction or spice blends.',
            1, 1, 'Green Earth Store, Ludhiana', '🌱'
        ),
        (
            1, 'Fresh Ginger (Adrak)', 'Spices & Herbs', 'Rio de Janeiro Variety',
            90.00, 'kg', 2.0, 150.0, '2026-10-17', 'Available Now',
            'Aromatic, fibrous and juicy raw ginger with thin skin. Clean washed and dried.',
            1, 1, 'Patel Farm Hub, Anand', '🫚'
        ),
        (
            2, 'Farm Fresh Green Chillies', 'Vegetables', 'G4 Spicy',
            40.00, 'kg', 3.0, 180.0, '2026-10-18', 'Available Now',
            'Dark green, spicy chillies freshly harvested this morning. Firm stems and high shelf life.',
            0, 1, 'Pimpalgaon Baswant, Nashik', '🌶️'
        ),
        (
            3, 'Pure Desi Cow Ghee (A2 Bilona)', 'Organic Specials', 'Gir Cow Cultured A2 Ghee',
            1400.00, 'kg', 1.0, 45.0, '2026-10-15', 'Available Now',
            'Prepared from whole curd using traditional wooden churner (Bilona method) over slow cow dung fire. Golden and granular.',
            1, 1, 'Green Earth Dairy Unit, Ludhiana', '🧈'
        )
    ]

    c.executemany('''
        INSERT INTO crops (
            farmer_id, crop_name, category, variety, price_per_unit, unit,
            min_order_qty, available_qty, harvest_date, status, description,
            organic, delivery_available, pickup_location, image_emoji
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', crops)

    # 4. Mandi reference prices
    mandi_data = [
        ('Tomatoes', 'Vegetables', 'Anand APMC', 'Anand', 32.00, 24.00, 36.00, 'kg', '2026-10-18'),
        ('Green Bell Peppers', 'Vegetables', 'Ahmedabad APMC', 'Ahmedabad', 52.00, 40.00, 58.00, 'kg', '2026-10-18'),
        ('Red Onions', 'Vegetables', 'Lasalgaon APMC', 'Nashik', 31.00, 22.00, 35.00, 'kg', '2026-10-18'),
        ('Black Grapes', 'Fruits', 'Nashik Fruit Mandi', 'Nashik', 98.00, 75.00, 115.00, 'kg', '2026-10-17'),
        ('Pomegranates', 'Fruits', 'Vashi APMC', 'Navi Mumbai', 135.00, 100.00, 160.00, 'kg', '2026-10-18'),
        ('Sharbati Wheat', 'Grains & Pulses', 'Khanna Grain Market', 'Ludhiana', 46.00, 40.00, 50.00, 'kg', '2026-10-16'),
        ('Basmati Rice 1121', 'Grains & Pulses', 'Karnal Mandi', 'Karnal', 110.00, 90.00, 125.00, 'kg', '2026-10-17'),
        ('Green Chillies', 'Vegetables', 'Pune APMC', 'Pune', 48.00, 35.00, 55.00, 'kg', '2026-10-18'),
        ('Fresh Ginger', 'Spices & Herbs', 'Surat APMC', 'Surat', 105.00, 85.00, 120.00, 'kg', '2026-10-18'),
        ('Mustard Seeds', 'Spices & Herbs', 'Ludhiana Mandi', 'Ludhiana', 88.00, 74.00, 95.00, 'kg', '2026-10-16')
    ]

    c.executemany('''
        INSERT INTO mandi_prices (crop_name, category, mandi_name, district, modal_price, min_price, max_price, unit, date_reported)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', mandi_data)

    # 5. Sample Inquiry
    c.execute('''
        INSERT INTO inquiries (
            crop_id, farmer_id, consumer_id, consumer_name, consumer_phone,
            consumer_email, requested_qty, delivery_address, message, status
        ) VALUES (1, 1, 4, 'Priya Sharma', '9819001122', 'priya@consumer.com', 25.0,
                  'Flat 402, Green Meadows, Bandra West, Mumbai',
                  'Looking for 25kg fresh organic tomatoes for our housing society weekly group buy. Can you ship or arrange delivery this Saturday?',
                  'Confirmed')
    ''')

    # 6. Farming Tips
    tips = [
        (
            'Direct Farm-to-Consumer Packaging Tips',
            'Post-Harvest Management',
            '3 min',
            'Use ventilated crates for delicate tomatoes and grapes to reduce transit bruising. Grade your produce into two sizes: Grade A commands a 20-30% premium among direct consumers.',
            'KisanDirect Agronomy Team'
        ),
        (
            'Setting Fair Direct Prices Without Middlemen',
            'Pricing Strategy',
            '4 min',
            'Check local APMC modal rates before pricing. Pricing 10-15% below retail supermarket prices gives consumers unmatched freshness and savings while giving you 30-40% higher returns than wholesale commission agents.',
            'Agri Marketing Cell'
        ),
        (
            'Organic Pest Control with Neem & Dashparni Ark',
            'Natural Farming',
            '5 min',
            'Prepare a concentrated neem seed kernel extract (5% NSKE) to repel sucking pests like whiteflies and thrips in tomato and chilli crops. Spray early morning or after sunset for best efficacy.',
            'Organic Farming Advisory'
        ),
        (
            'Proper Storage Techniques for Nashik Onions',
            'Storage & Shelf Life',
            '3 min',
            'Ensure late-kharif onions are cured in shaded, well-ventilated structures for 10-15 days. Avoid bagging before moisture content in outer skin falls below 12% to prevent black mould (Aspergillus niger).',
            'Post Harvest Research Station'
        )
    ]

    c.executemany('''
        INSERT INTO farming_tips (title, category, read_time, content, author)
        VALUES (?, ?, ?, ?, ?)
    ''', tips)

    conn.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized and seeded successfully.")
