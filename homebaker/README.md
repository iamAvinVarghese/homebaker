# Home Baker Cake Ordering & Management System

A comprehensive Django-based web application for cake ordering and management with advanced features including AI recommendations, analytics, multi-role authentication, and a complete admin panel.

## 🎯 Features

### 1. **User Authentication**
- Customer, Baker, and Admin roles
- Separate login for each role
- OTP login simulation
- Secure password hashing
- Account lock after 5 failed attempts
- Session handling

### 2. **Customer Module**
- Home page with featured cakes
- Cake listing with advanced filters (flavor, occasion, price range)
- Search system
- Shopping cart functionality
- Order placement with customization
- Order tracking with timeline UI
- Wallet system for payments
- Order history
- Review & rating system
- Photo upload after delivery
- AI-powered cake recommendations

### 3. **Baker Module**
- Comprehensive dashboard with KPIs:
  - Total Orders
  - Monthly Revenue
  - Total Profit
  - Average Rating
- Interactive charts (Chart.js):
  - Monthly Revenue (Line Chart)
  - Expenses (Bar Chart)
  - Profit (Line Chart)
  - Popular Cakes (Donut Chart)
- Cake management (Add, Edit, Stock)
- Expense tracking
- Order handling and status updates
- Performance reports
- Notifications

### 4. **Admin Module (Dark Theme Panel)**
- Dark-themed admin dashboard
- System analytics and overview
- Revenue overview
- Manage bakers (Approve/Reject/Suspend)
- Manage customers
- Platform commission tracking
- Audit logs for all actions
- Advanced analytics page

### 5. **Order Management**
- Status tracking: Confirmed → Baking → Packing → Out for Delivery → Delivered
- Delivery timeline UI
- Bulk orders support
- Auto stock update

### 6. **Analytics & Data Science**
- Revenue aggregation
- Profit calculation
- Growth prediction (simple ML)
- Demand prediction
- Customer retention metrics
- Monthly reports

### 7. **AI Features**
- Recommendation system based on:
  - Order history
  - Ratings
  - Popularity
- Smart pricing suggestions
- Auto business insights
- Trending cake detection
- Low stock prediction

### 8. **Security**
- Role-based permissions
- Admin action logs
- CSRF protection
- Input validation
- Account lock mechanism

## 🛠️ Tech Stack

- **Backend**: Django 4.2+
- **Frontend**: Bootstrap 5 + Custom CSS
- **Charts**: Chart.js
- **Database**: SQLite (dev) / PostgreSQL (prod ready)
- **Authentication**: Django Auth + OTP (mock)
- **AI Layer**: Python-based recommendation & insights

## 📦 Installation

### Prerequisites
- Python 3.8+
- pip
- virtualenv (recommended)

### Setup Steps

1. **Clone the repository**
```bash
cd homebaker
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r REQUIREMENTS.txt
```

4. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create superuser**
```bash
python manage.py createsuperuser
```

6. **Seed sample data (optional)**
```bash
python manage.py seed_data
```

7. **Run development server**
```bash
python manage.py runserver
```

8. **Access the application**
- Home: http://127.0.0.1:8000/
- Admin Panel: http://127.0.0.1:8000/admin/
- Admin Dashboard: http://127.0.0.1:8000/admin-panel/ (requires staff login)

## 👥 User Roles & Access

### Customer
- Register/Login
- Browse and search cakes
- Add to cart and checkout
- Track orders
- Add reviews
- Manage wallet

### Baker
- Register as baker (requires admin approval)
- Manage cakes (add/edit/stock)
- Track expenses
- Handle orders
- View analytics dashboard
- Receive notifications

### Admin
- Full system access
- Approve/reject bakers
- Suspend/unsuspend users
- View system analytics
- Audit logs
- Manage platform settings

## 📊 Database Models

- **UserProfile**: Extended user profile with role and security features
- **BakerProfile**: Baker-specific information and status
- **Cake**: Cake catalog with ratings and stock
- **CakeSize**: Size options with price multipliers
- **Order**: Order management with status tracking
- **OrderItem**: Individual items in orders
- **Expense**: Baker expense tracking
- **Review**: Customer reviews and ratings
- **Wallet**: Wallet transaction system
- **Notification**: User notifications
- **AuditLog**: Admin action logging
- **OTP**: OTP verification system

## 🔐 Security Features

1. **Account Lock**: Accounts lock after 5 failed login attempts
2. **Role-Based Access**: Views protected by role checks
3. **CSRF Protection**: Django CSRF middleware enabled
4. **Input Validation**: Form and model-level validation
5. **Audit Logging**: All admin actions are logged

## 📈 Analytics & AI

### Recommendation Engine
- Personalized recommendations based on order history
- Trending cakes detection
- Popular cakes by ratings

### Business Insights
- Revenue analytics
- Profit calculations
- Growth predictions
- Demand forecasting
- Low stock alerts

### Smart Pricing
- Market-based price suggestions
- Competitor analysis
- Optimal pricing recommendations

## 🎨 UI/UX Features

- Responsive design (mobile-friendly)
- Dark/Light theme toggle
- Modern Bootstrap 5 UI
- Interactive Chart.js visualizations
- Smooth animations and transitions
- User-friendly navigation

## 📝 API Endpoints

### Authentication
- `POST /login/` - User login
- `POST /logout/` - User logout
- `POST /register/` - User registration
- `POST /send-otp/` - Send OTP

### Customer
- `GET /` - Home page
- `GET /cakes/` - Cake listing
- `POST /cart/add/<cake_id>/` - Add to cart
- `GET /cart/` - View cart
- `POST /checkout/` - Checkout
- `GET /order-tracking/<order_id>/` - Track order
- `GET /my-orders/` - Order history
- `POST /review/<order_id>/` - Add review
- `GET /wallet/` - Wallet management

### Baker
- `GET /baker/dashboard/` - Baker dashboard
- `GET /baker/cakes/` - Manage cakes
- `POST /baker/cakes/add/` - Add cake
- `POST /baker/expenses/` - Manage expenses
- `GET /baker/orders/` - Manage orders
- `POST /baker/orders/<order_id>/update-status/` - Update order status

### Admin
- `GET /admin-panel/` - Admin dashboard
- `GET /admin-panel/users/` - Manage users
- `GET /admin-panel/bakers/` - Manage bakers
- `POST /admin-panel/bakers/<baker_id>/approve/` - Approve baker
- `GET /admin-panel/audit-logs/` - View audit logs
- `GET /admin-panel/analytics/` - Advanced analytics

## 🧪 Testing

### Demo Credentials

**Customer:**
- Username: `john_doe`
- Password: `password123`
- OTP (Login): `654321`
- OTP (Register): `123456`

**Baker:**
- Username: `baker_alice`
- Password: `password123`

**Admin:**
- Create via: `python manage.py createsuperuser`

## 🚀 Deployment

### Production Checklist

1. **Settings Configuration**
   - Set `DEBUG = False`
   - Configure `ALLOWED_HOSTS`
   - Use environment variables for `SECRET_KEY`
   - Set up PostgreSQL database

2. **Static Files**
   - Run `python manage.py collectstatic`
   - Configure static file serving (WhiteNoise or CDN)

3. **Media Files**
   - Configure media file storage (AWS S3 recommended)

4. **Security**
   - Use HTTPS
   - Configure CORS if needed
   - Set secure cookie flags

5. **Database**
   - Migrate to PostgreSQL
   - Set up database backups

6. **Server**
   - Use Gunicorn or uWSGI
   - Configure Nginx as reverse proxy
   - Set up SSL certificates

## 📚 Documentation

### Architecture
- Modular view structure (`views_auth.py`, `views_customer.py`, `views_baker.py`, `views_admin.py`)
- AI utilities in `ai_utils.py`
- Centralized forms in `forms.py`
- Comprehensive models in `models.py`

### Key Files
- `models.py`: Database models
- `views_*.py`: View modules by feature
- `forms.py`: Form definitions
- `ai_utils.py`: AI and analytics utilities
- `admin.py`: Django admin configuration
- `urls.py`: URL routing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is for educational purposes.

## 👨‍💻 Author

Built as a comprehensive final year project demonstrating:
- Full-stack development
- Database design
- AI/ML integration
- Analytics and reporting
- Security best practices
- Modern web development

## 📞 Support

For issues or questions, please open an issue in the repository.

---

**Note**: This is a demonstration project. For production use, implement proper OTP service integration, payment gateway integration, and enhanced security measures.
