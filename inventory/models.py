from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import F, Sum

class User(AbstractUser):
    is_admin = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('name', 'category')
    
    def __str__(self):
        return f"{self.name} ({self.category})"

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT)
    model_number = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    hsn_code = models.CharField(max_length=50)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-last_updated']
    
    def __str__(self):
        return f"{self.name} - {self.brand}"
    
    @property
    def stock_status(self):
        if self.quantity == 0:
            return 'out_of_stock'
        elif self.quantity <= self.low_stock_threshold:
            return 'low_stock'
        return 'in_stock'
    
    @property
    def total_value(self):
        return self.selling_price * self.quantity

class Sale(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('online', 'Online'),
        ('finance', 'Finance'),
        ('pinelabs', 'Pinelabs Card'),
        ('upi', 'UPI'),
        ('partial', 'Partial Payment'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=100, default='Retail Sale')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    customer_name = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=15, blank=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.product} - {self.quantity} units"
    
    @property
    def total_amount(self):
        return self.sale_price * self.quantity
    
    @property
    def pending_amount(self):
        if self.payment_method in ['finance', 'partial']:
            return self.total_amount - (self.amount_paid or 0)
        return 0