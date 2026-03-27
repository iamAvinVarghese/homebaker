from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date
from .models import (
    Cake, Order, OrderItem, UserProfile, BakerProfile, Expense, Review,
    Wallet, CakeSize, CustomCakeRequest, SupportTicket, WebsiteReview
)


# Registration Form
class RegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'placeholder': 'Enter your full name'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control form-control-lg',
        'placeholder': 'Enter your email'
    }))
    phone_number = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter phone number',
        'id': 'id_phone_number'
    }))
    # OTP is now sent via email after registration - no OTP field here
    role = forms.ChoiceField(
        choices=[('customer', 'Customer'), ('baker', 'Baker')],
        initial='customer',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = ['password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control form-control-lg'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control form-control-lg'})
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if User.objects.filter(username=phone_number).exists():
             raise forms.ValidationError("This phone number is already registered.")
        return phone_number


# Login Form (Password)
class PasswordLoginForm(forms.Form):
    phone_number = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'placeholder': 'Phone Number'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control form-control-lg',
        'placeholder': 'Password'
    }))


# Login Form (OTP)
class OTPLoginForm(forms.Form):
    phone_number = forms.CharField(max_length=15, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter phone number'
    }))
    otp = forms.CharField(max_length=6, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'placeholder': 'Enter OTP'
    }))


# Order Form (Legacy - kept for backward compatibility, but cart/checkout is preferred)
class OrderForm(forms.ModelForm):
    """Legacy order form - Use cart/checkout flow instead"""
    class Meta:
        model = Order
        fields = ['delivery_date', 'delivery_address']
        widgets = {
            'delivery_date': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date'
            }),
            'delivery_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Enter delivery address'
            }),
        }
    
    def clean_delivery_date(self):
        delivery_date = self.cleaned_data.get('delivery_date')
        if delivery_date and delivery_date < date.today():
            raise forms.ValidationError("Delivery date cannot be in the past.")
        return delivery_date


# Baker Registration Form
class BakerRegistrationForm(RegistrationForm):
    shop_name = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'placeholder': 'Enter shop name'
    }))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': '3',
        'placeholder': 'Enter shop address'
    }))
    city = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'placeholder': 'Enter city'
    }))
    pincode = forms.CharField(max_length=10, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'placeholder': 'Enter pincode'
    }))
    license_number = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'placeholder': 'Enter FSSAI License Number'
    }))
    fssai_certificate = forms.FileField(required=False, widget=forms.FileInput(attrs={
        'class': 'form-control',
        'accept': 'image/*'
    }))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Keep widget visible so it doesn't vanish on validation errors
        self.fields['role'].widget = forms.RadioSelect(attrs={'class': 'form-check-input'})

    def clean_license_number(self):
        license_number = self.cleaned_data.get('license_number')
        if license_number:
            if BakerProfile.objects.filter(license_number=license_number).exists():
                raise forms.ValidationError("already synced and verification failed")
        return license_number

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        
        if role == 'baker':
            shop_name = cleaned_data.get('shop_name')
            address = cleaned_data.get('address')
            city = cleaned_data.get('city')
            pincode = cleaned_data.get('pincode')
            
            if not shop_name:
                self.add_error('shop_name', 'Shop name is required for bakers.')
            if not address:
                self.add_error('address', 'Address is required for bakers.')
            if not city:
                self.add_error('city', 'City is required for bakers.')
            if not pincode:
                self.add_error('pincode', 'Pincode is required for bakers.')
            
            # FSSAI Field Validation (Presence only - AI verification done via AJAX before registration)
            license_number = cleaned_data.get('license_number')
            fssai_certificate = cleaned_data.get('fssai_certificate')
            
            if not license_number:
                self.add_error('license_number', 'FSSAI License Number is required for bakers.')
            if not fssai_certificate:
                self.add_error('fssai_certificate', 'FSSAI Certificate image is required for bakers.')
        
        return cleaned_data


# Expense Form
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'description', 'amount', 'expense_date', 'receipt']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter expense description'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'expense_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'receipt': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount


# Review Form
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment', 'photo']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5',
                'step': '0.5'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Share your experience...'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }


# Wallet Recharge Form
class WalletRechargeForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(100)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'step': '100',
            'min': '100',
            'placeholder': 'Minimum ₹100'
        })
    )
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount < 100:
            raise forms.ValidationError("Minimum recharge amount is ₹100.")
        return amount


# Wallet Withdraw Form
class WalletWithdrawForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(1)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'step': '1',
            'min': '1',
            'placeholder': 'Amount to withdraw'
        })
    )
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Withdrawal amount must be greater than zero.")
        return amount


# Cake Form (for baker to add/edit cakes)
class CakeForm(forms.ModelForm):
    class Meta:
        model = Cake
        fields = ['name', 'flavor', 'occasion', 'price', 'description', 'image', 'image_url', 'is_available']
        labels = {
            'price': 'Price (per kg)',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'flavor': forms.Select(attrs={'class': 'form-select'}),
            'occasion': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Price per kg'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Or enter image URL'
            }),

            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price


# Search Form
class CakeSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search cakes...'
        })
    )
    flavor = forms.ChoiceField(
        required=False,
        choices=[('', 'All Flavors')] + Cake.FLAVOR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    occasion = forms.ChoiceField(
        required=False,
        choices=[('', 'All Occasions')] + Cake.OCCASION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    min_price = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min Price/kg',
            'step': '0.01'
        })
    )
    max_price = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max Price/kg',
            'step': '0.01'
        })
    )
    top_rated = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Sort By'),
            ('price_asc', 'Price: Low to High'),
            ('price_desc', 'Price: High to Low'),
            ('rating', 'Top Rated'),
            ('newest', 'Newest Arrivals')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


# User Profile Form
class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email Address'
    }))
    default_address = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': '3',
        'placeholder': 'Default Delivery Address'
    }))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['default_address'].initial = self.instance.profile.default_address
            # Add profile picture field manually since it's on the profile model, not User
            self.fields['profile_picture'] = forms.ImageField(
                required=False,
                widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
            )
    
    def save(self, commit=True):
        user = super().save(commit=commit)
        if hasattr(user, 'profile'):
            user.profile.default_address = self.cleaned_data['default_address']
            print(f"DEBUG: cleaned_data keys: {self.cleaned_data.keys()}")
            print(f"DEBUG: profile_picture data: {self.cleaned_data.get('profile_picture')}")
            if self.cleaned_data.get('profile_picture'):
                user.profile.profile_picture = self.cleaned_data['profile_picture']
            user.profile.save()
        return user


# Baker Profile Form
class BakerProfileForm(forms.ModelForm):
    shop_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}))
    city = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    pincode = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    license_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))
    fssai_certificate = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    accepts_custom_orders = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}), label="I accept custom cake orders")

    class Meta:
        model = BakerProfile
        fields = ['shop_name', 'address', 'city', 'pincode', 'license_number', 'fssai_certificate', 'accepts_custom_orders']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make license number read-only as per plan assumption/best practice
        if self.instance and self.instance.pk:
            self.fields['license_number'].widget.attrs['readonly'] = True
            self.fields['license_number'].help_text = "Contact support to update FSSAI License Number"


# Custom Cake Form
class CustomCakeForm(forms.Form):
    size = forms.ChoiceField(
        choices=[('0.5kg', '0.5 kg'), ('1kg', '1 kg'), ('2kg', '2 kg'), ('3kg', '3 kg'), ('5kg+', '5 kg+')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    shape = forms.ChoiceField(
        choices=[('Round', 'Round'), ('Square', 'Square'), ('Heart', 'Heart'), ('Rectangular', 'Rectangular'), ('Tall', 'Tall'), ('Tiered', 'Tiered'), ('Custom', 'Custom Shape')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    flavor = forms.ChoiceField(
        choices=Cake.FLAVOR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    occasion = forms.ChoiceField(
        choices=Cake.OCCASION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    primary_colors = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Pastel Pink & Gold'
        })
    )
    design_style = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Minimalist, Floral, Superhero, Vintage'
        })
    )
    message_on_cake = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Happy Birthday Avin'
        })
    )
    extra_instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '3',
            'placeholder': 'Any specific details? e.g., Eggless, Less Fondant'
        })
    )


# Photo Custom Cake Form
class PhotoCustomCakeForm(forms.ModelForm):
    flavor = forms.ChoiceField(
        choices=Cake.FLAVOR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = CustomCakeRequest
        fields = ['reference_image', 'description', 'flavor', 'size', 'delivery_date']
        widgets = {
            'reference_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '3', 'placeholder': 'Describe the cake design...'}),
            'size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1kg, 2kg'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


# Delivery Verification Form
class DeliveryVerificationForm(forms.Form):
    otp = forms.CharField(max_length=4, min_length=4, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg text-center',
        'placeholder': 'Enter 4-digit OTP',
        'pattern': '[0-9]{4}',
        'maxlength': '4',
        'autocomplete': 'off'
    }))

    def clean_otp(self):
        otp = self.cleaned_data.get('otp')
        if otp and (not otp.isdigit() or len(otp) != 4):
            raise forms.ValidationError("OTP must be a 4-digit number.")
        return otp

# Password Change Form
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control form-control-lg'})


# Support Ticket Form
class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'description']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief summary of the issue'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Detailed description of the problem'
            }),
        }

# Website Review Form
class WebsiteReviewForm(forms.ModelForm):
    class Meta:
        model = WebsiteReview
        fields = ['rating', 'review_text']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5',
                'step': '1'
            }),
            'review_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Share your feedback about our website...'
            }),
        }
