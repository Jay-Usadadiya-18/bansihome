# inventory/management/commands/populate_data.py
from django.core.management.base import BaseCommand
from inventory.models import Category, Brand

class Command(BaseCommand):
    help = 'Populates initial categories and brands'
    
    def handle(self, *args, **options):
        # Create categories
        ac = Category.objects.create(name='Air Conditioner')
        wm = Category.objects.create(name='Washing Machine')
        rf = Category.objects.create(name='Refrigerator')
        tv = Category.objects.create(name='Television')
        ac = Category.objects.create(name='ATA Chakki')
        
        # Create brands
        Brand.objects.create(name='Godrej', category=ac)
        Brand.objects.create(name='LG', category=ac)
        Brand.objects.create(name='Samsung', category=ac)
        Brand.objects.create(name='Whirlpool', category=wm)
        Brand.objects.create(name='Tansui', category=tv)
        
        self.stdout.write(self.style.SUCCESS('Successfully populated initial data'))