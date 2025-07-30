from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import F, Sum, Count
from django.db import transaction
from .models import User, Category, Brand, Product, Sale
from .serializers import (
    UserSerializer, 
    CategorySerializer, 
    BrandSerializer, 
    ProductSerializer, 
    SaleSerializer
)
from .permissions import IsAdminOrManager

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get_queryset(self):
        if self.request.user.is_admin:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.select_related('category')
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('brand', 'category')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by stock status
        status = self.request.query_params.get('status')
        if status == 'low_stock':
            queryset = queryset.filter(quantity__lte=F('low_stock_threshold'))
        elif status == 'out_of_stock':
            queryset = queryset.filter(quantity=0)
        
        # Filter by category
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        # Filter by brand
        brand_id = self.request.query_params.get('brand_id')
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        stats = {
            'total_products': Product.objects.count(),
            'total_inventory_value': Product.objects.aggregate(
                total=Sum(F('quantity') * F('selling_price'))
            )['total'] or 0,
            'low_stock_count': Product.objects.filter(
                quantity__lte=F('low_stock_threshold')
            ).count(),
            'out_of_stock_count': Product.objects.filter(
                quantity=0
            ).count(),
        }
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        product = self.get_object()
        quantity = request.data.get('quantity', 0)
        
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response(
                {'error': 'Invalid quantity'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product.quantity += quantity
        product.save()
        
        return Response({
            'status': 'Stock updated',
            'new_quantity': product.quantity
        })

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.select_related('product')
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        with transaction.atomic():
            sale = serializer.save()
            product = sale.product
            product.quantity -= sale.quantity
            product.save()
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        # Sales by category
        by_category = (
            Sale.objects
            .values('product__category__name')
            .annotate(
                total_sales=Sum(F('quantity') * F('sale_price')),
                total_quantity=Sum('quantity')
            )
            .order_by('-total_sales')
        )
        
        # Monthly sales
        monthly_sales = (
            Sale.objects
            .extra({'month': "strftime('%Y-%m', date)"})
            .values('month')
            .annotate(
                total_sales=Sum(F('quantity') * F('sale_price')),
                total_quantity=Sum('quantity')
            )
            .order_by('month')
        )
        
        # Top products
        top_products = (
            Sale.objects
            .values('product__name', 'product__brand__name')
            .annotate(
                total_sales=Sum(F('quantity') * F('sale_price')),
                total_quantity=Sum('quantity')
            )
            .order_by('-total_sales')[:5]
        )
        
        return Response({
            'by_category': by_category,
            'monthly_sales': monthly_sales,
            'top_products': top_products,
        })