"""
Data Seeder Command
Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import random

from main.models import (
    User, UserProfile, BakerProfile, Cake, CakeSize, Order, OrderItem,
    Expense, Review, Wallet, Notification
)


class Command(BaseCommand):
    help = 'Seed database with essential data (admin + cake sizes only)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up admin and base data...'))

        # Create essential cake sizes
        self.create_cake_sizes()

        # Create admin account only
        self.create_admin()

        self.stdout.write(self.style.SUCCESS('Setup completed! Admin is ready.'))

    def create_admin(self):
        """Create or update the admin user"""
        phone = '1234567890'
        user, created = User.objects.get_or_create(
            username=phone,
            defaults={
                'email': 'admin@homebaker.com',
                'first_name': 'System',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        # Always ensure password and permissions are up to date
        user.set_password('aaaaaa12')
        user.is_staff = True
        user.is_superuser = True
        user.save()
            
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'phone_number': phone,
                'role': 'admin',
                'is_phone_verified': True,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'Admin user ready with phone: {phone}'))

    def create_cake_sizes(self):
        """Create cake sizes"""
        sizes = [
            ('small', Decimal('0.7')),
            ('medium', Decimal('1.0')),
            ('large', Decimal('1.5')),
            ('xlarge', Decimal('2.0')),
        ]

        created = []
        for size_code, multiplier in sizes:
            size, created_flag = CakeSize.objects.get_or_create(
                size=size_code,
                defaults={'multiplier': multiplier}
            )
            created.append(size)
            if created_flag:
                self.stdout.write(f'Created cake size: {size.get_size_display()}')

        return created

    def create_customers(self):
        """Create sample customers"""
        customers_data = [
            {'username': 'john_doe', 'email': 'john@example.com', 'phone': '9876543210', 'name': 'John Doe'},
            {'username': 'jane_smith', 'email': 'jane@example.com', 'phone': '9876543211', 'name': 'Jane Smith'},
            {'username': 'mike_wilson', 'email': 'mike@example.com', 'phone': '9876543212', 'name': 'Mike Wilson'},
            {'username': 'sarah_jones', 'email': 'sarah@example.com', 'phone': '9876543213', 'name': 'Sarah Jones'},
            {'username': 'david_brown', 'email': 'david@example.com', 'phone': '9876543214', 'name': 'David Brown'},
        ]

        customers = []
        for data in customers_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['name'],
                }
            )
            if created:
                user.set_password('password123')
                user.save()

            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'phone_number': data['phone'],
                    'role': 'customer',
                    'is_phone_verified': True,
                }
            )
            customers.append(user)
            if created:
                self.stdout.write(f'Created customer: {data["name"]}')

        return customers

    def create_bakers(self):
        """Create sample bakers"""
        bakers_data = [
            {
                'username': 'baker_alice', 'email': 'alice@bakery.com', 'phone': '9876543220',
                'name': 'Alice Baker', 'shop': 'Sweet Dreams Bakery', 'city': 'Mumbai'
            },
            {
                'username': 'baker_bob', 'email': 'bob@bakery.com', 'phone': '9876543221',
                'name': 'Bob Baker', 'shop': 'Delicious Cakes', 'city': 'Delhi'
            },
            {
                'username': 'baker_carol', 'email': 'carol@bakery.com', 'phone': '9876543222',
                'name': 'Carol Baker', 'shop': 'Heavenly Treats', 'city': 'Bangalore'
            },
        ]

        bakers = []
        for data in bakers_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['name'],
                }
            )
            if created:
                user.set_password('password123')
                user.save()

            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'phone_number': data['phone'],
                    'role': 'baker',
                    'is_phone_verified': True,
                }
            )

            baker_profile, created = BakerProfile.objects.get_or_create(
                user_profile=profile,
                defaults={
                    'shop_name': data['shop'],
                    'address': f'{data["shop"]}, {data["city"]}',
                    'city': data['city'],
                    'pincode': '110001',
                    'status': 'approved',
                    'commission_rate': Decimal('10.00'),
                }
            )
            bakers.append(user)
            if created:
                self.stdout.write(f'Created baker: {data["shop"]}')

        return bakers

    def create_cakes(self, bakers):
        """Create sample cakes"""
        cake_data = [
            {'name': 'Chocolate Fudge Cake', 'flavor': 'chocolate', 'occasion': 'birthday', 'price': 500},
            {'name': 'Vanilla Delight', 'flavor': 'vanilla', 'occasion': 'birthday', 'price': 450},
            {'name': 'Red Velvet Special', 'flavor': 'red_velvet', 'occasion': 'anniversary', 'price': 600},
            {'name': 'Strawberry Dream', 'flavor': 'strawberry', 'occasion': 'birthday', 'price': 550},
            {'name': 'Wedding White Cake', 'flavor': 'vanilla', 'occasion': 'wedding', 'price': 2000},
            {'name': 'Black Forest', 'flavor': 'black_forest', 'occasion': 'birthday', 'price': 650},
            {'name': 'Pineapple Cake', 'flavor': 'pineapple', 'occasion': 'custom', 'price': 500},
            {'name': 'Mango Delight', 'flavor': 'mango', 'occasion': 'festival', 'price': 550},
        ]

        cakes = []
        for data in cake_data:
            baker = random.choice(bakers)
            cake, created = Cake.objects.get_or_create(
                name=data['name'],
                defaults={
                    'flavor': data['flavor'],
                    'occasion': data['occasion'],
                    'price': Decimal(str(data['price'])),
                    'description': f'A delicious {data["flavor"]} cake perfect for {data["occasion"]} occasions.',
                    'is_available': True,
                    'baker': baker,
                }
            )
            cakes.append(cake)
            if created:
                self.stdout.write(f'Created cake: {data["name"]}')

        return cakes

    def create_orders(self, customers, cakes):
        """Create sample orders"""
        orders = []
        statuses = ['pending', 'confirmed', 'baking', 'packing', 'out_for_delivery', 'delivered']

        for i in range(20):
            customer = random.choice(customers)
            cake = random.choice(cakes)
            quantity = random.randint(1, 3)
            days_ago = random.randint(0, 30)
            order_date = timezone.now() - timedelta(days=days_ago)
            delivery_date = date.today() + timedelta(days=random.randint(1, 7))
            status = random.choice(statuses)

            order = Order.objects.create(
                customer=customer,
                delivery_date=delivery_date,
                delivery_address=f'Address {random.randint(1, 100)}, City',
                delivery_charge=Decimal('50.00'),
                status=status,
                payment_status='paid' if status != 'pending' else 'pending',
                payment_method='wallet',
                created_at=order_date,
                total_amount=Decimal('0.00'),
            )

            # Create order item
            OrderItem.objects.create(
                order=order,
                cake=cake,
                quantity=quantity,
                unit_price=cake.price,
                subtotal=cake.price * quantity,
            )

            order.subtotal = cake.price * quantity
            order.total_amount = order.subtotal + order.delivery_charge
            order.save()

            orders.append(order)

        self.stdout.write(f'Created {len(orders)} orders')
        return orders

    def create_reviews(self, orders):
        """Create sample reviews"""
        delivered_orders = [o for o in orders if o.status == 'delivered']
        review_count = 0

        for order in delivered_orders[:10]:  # Review first 10 delivered orders
            if not hasattr(order, 'review'):
                order_item = order.items.first()
                if order_item:
                    Review.objects.create(
                        order=order,
                        cake=order_item.cake,
                        customer=order.customer,
                        rating=random.randint(4, 5),
                        comment=f'Great cake! Very satisfied with the order.',
                        is_approved=True,
                    )
                    review_count += 1

        self.stdout.write(f'Created {review_count} reviews')

    def create_expenses(self, bakers):
        """Create sample expenses"""
        categories = ['ingredients', 'packaging', 'delivery', 'utilities', 'equipment', 'marketing']
        expense_count = 0

        for baker in bakers:
            for i in range(5):
                expense_date = date.today() - timedelta(days=random.randint(0, 30))
                Expense.objects.create(
                    baker=baker,
                    category=random.choice(categories),
                    description=f'Sample expense {i+1}',
                    amount=Decimal(str(random.randint(100, 5000))),
                    expense_date=expense_date,
                )
                expense_count += 1

        self.stdout.write(f'Created {expense_count} expenses')

    def create_wallet_transactions(self, customers):
        """Create sample wallet transactions"""
        for customer in customers:
            # Recharge
            Wallet.add_transaction(
                user=customer,
                transaction_type='credit',
                amount=Decimal('1000.00'),
                source='recharge',
                description='Initial wallet recharge'
            )

        self.stdout.write(f'Created wallet transactions for {len(customers)} customers')
