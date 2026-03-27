# Setup Guide - Home Baker System

## Quick Start

### 1. Install Dependencies
```bash
pip install -r REQUIREMENTS.txt
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Superuser
```bash
python manage.py createsuperuser
```
Enter username, email, and password when prompted.

### 4. Seed Sample Data (Optional)
```bash
python manage.py seed_data
```

This will create:
- 5 sample customers
- 3 sample bakers
- 8 sample cakes
- 20 sample orders
- Reviews, expenses, and wallet transactions

### 5. Run Server
```bash
python manage.py runserver
```

### 6. Access the Application
- Home: http://127.0.0.1:8000/
- Django Admin: http://127.0.0.1:8000/admin/
- Admin Dashboard: http://127.0.0.1:8000/admin-panel/ (login as superuser)

## Demo Credentials

After running `seed_data`, you can use:

**Customer:**
- Username: `john_doe`
- Password: `password123`

**Baker:**
- Username: `baker_alice`
- Password: `password123`

**Admin:**
- Create via: `python manage.py createsuperuser`

## OTP Codes (Demo)

- Registration OTP: `123456`
- Login OTP: `654321`

## Testing the Features

### Customer Flow
1. Register/Login as customer
2. Browse cakes at `/cakes/`
3. Add cakes to cart
4. View cart at `/cart/`
5. Checkout and place order
6. Track order at `/order-tracking/<order_id>/`
7. Add review after delivery
8. Recharge wallet at `/wallet/`

### Baker Flow
1. Register as baker (status: pending)
2. Login as admin and approve baker at `/admin-panel/bakers/`
3. Login as baker
4. Access dashboard at `/baker/dashboard/`
5. Add cakes at `/baker/cakes/add/`
6. Manage expenses at `/baker/expenses/`
7. Handle orders at `/baker/orders/`
8. Update order status

### Admin Flow
1. Login as superuser
2. Access admin dashboard at `/admin-panel/`
3. View system analytics
4. Approve/reject bakers
5. Suspend/unsuspend users
6. View audit logs

## Common Issues

### Issue: No module named 'main'
**Solution:** Make sure you're in the `homebaker` directory (where `manage.py` is)

### Issue: Migration errors
**Solution:** 
```bash
python manage.py makemigrations main
python manage.py migrate
```

### Issue: Static files not loading
**Solution:** Ensure `STATICFILES_DIRS` is set correctly in `settings.py`

### Issue: Media files not uploading
**Solution:** Create `media` directory in project root:
```bash
mkdir media
```

## Production Deployment

See `README.md` for production deployment checklist.
