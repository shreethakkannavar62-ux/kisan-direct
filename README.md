# KisanDirect - Digital Farm-to-Consumer Platform 🌾

**KisanDirect** is a digital platform designed to connect farmers directly with consumers, restaurants, and retail buyers. By providing real-time crop availability, transparent pricing, APMC mandi benchmarks, and verified direct contact details (Phone & WhatsApp), the system eliminates middlemen margins, ensuring fair earnings for farmers and fresh savings for consumers.

---

## 🌟 Key Features

1. **Direct Crop Marketplace & Real-Time Availability**
   - Live availability tracking (in kg, quintals, dozens, or boxes).
   - Categorized by Vegetables, Fruits, Grains & Pulses, Spices & Herbs, and Organic Specials.
   - 100% Organic filter and harvest date freshness indicator.
   - Instant client-side search and filtering without page reloads.

2. **Transparent Direct Pricing & APMC Mandi Benchmarks**
   - Clear pricing per unit set directly by the farmer.
   - Interactive live price calculator (calculates total cost instantly as consumers adjust requested kg).
   - Real-time comparison with local APMC Mandi rates showing consumer savings and farmer margins.

3. **Direct Farmer Contact (Zero Intermediaries)**
   - Click-to-Call (`tel:`) direct farmer mobile dialing.
   - 1-Click WhatsApp messaging with pre-composed professional inquiry greetings.
   - Direct purchase inquiry form with location and delivery details sent to the farmer's portal.

4. **Dedicated Farmer Management Portal**
   - Secure dashboard showing active listings, available inventory, and incoming inquiries.
   - Add new harvest batches, edit prices, update stock, or mark crops as sold out.
   - Consumer inquiry manager with one-click status transitions (Pending, Confirmed, Completed, Cancelled).

5. **Consumer Inquiries Tracking**
   - Personal dashboard for consumers to monitor submitted inquiries and reconnect with farmers.

6. **Verified Farmers Directory**
   - Directory of verified regional growers with village locations and their complete crop catalogue.

7. **Agricultural & Post-Harvest Advisories**
   - Field tips on direct marketing, organic pest protection, post-harvest packaging, and storage.

---

## 🛠️ Technology Stack

- **Backend**: Python 3 (Flask)
- **Database**: SQLite3 (Embedded relational storage with foreign keys)
- **Frontend**: Semantic HTML5, Vanilla JavaScript (Dynamic price calculator, tabs, instant search, WhatsApp links)
- **Styling**: Vanilla CSS Design System with custom typography (`Plus Jakarta Sans` & `Outfit`), mobile-first responsive layout, and custom badges.

---

## 📂 Project Structure

```
farmer v 1.2/
├── app.py                      # Main Flask application and routing
├── database.py                 # SQLite database schema, helpers, and sample seed data
├── requirements.txt            # Python dependencies
├── farmer_market.db            # SQLite database file (created on init)
├── static/
│   ├── css/
│   │   └── style.css           # Modern agricultural design system CSS
│   ├── js/
│   │   └── main.js            # Client-side calculator, filters, and WhatsApp logic
│   └── images/
├── templates/
│   ├── base.html               # Main base layout with navbar and footer
│   ├── index.html              # Homepage with hero, live crops, and mandi ticker
│   ├── crops.html              # Full crop marketplace with live search & filters
│   ├── crop_detail.html        # Crop detail page with calculator and contact actions
│   ├── crop_form.html          # Form for farmers to add/edit crops
│   ├── farmer_dashboard.html   # Farmer portal (crop management & inquiry inbox)
│   ├── buyer_dashboard.html    # Consumer portal (my submitted inquiries)
│   ├── mandi_prices.html       # APMC Mandi benchmark comparison table
│   ├── farmers_directory.html  # Directory of verified local farmers
│   ├── tips.html               # Agronomy and harvesting tips
│   ├── login.html              # Authentication login page
│   └── register.html           # Dual-role registration (Farmer / Consumer)
└── README.md
```

---

## 🚀 Running the Project

1. **Activate your Python environment** and install requirements (if needed):
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Flask application**:
   ```bash
   python app.py
   ```

3. **Open in your web browser**:
   Navigate to: **`http://127.0.0.1:5000`**

---

## 🔑 Pre-Seeded Demo Accounts

| Role | Email | Password | Details |
|------|-------|----------|---------|
| **Farmer** | `ramesh@kisan.in` | `farmer123` | Ramesh Patel (Anand, Gujarat) |
| **Farmer** | `sunita@kisan.in` | `farmer123` | Sunita Shinde (Nashik, Maharashtra) |
| **Farmer** | `balwinder@kisan.in` | `farmer123` | Balwinder Singh (Ludhiana, Punjab) |
| **Consumer** | `priya@consumer.com` | `buyer123` | Priya Sharma (Mumbai, Maharashtra) |
