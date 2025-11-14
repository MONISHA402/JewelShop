from django.contrib import admin
from .models import Product, Category, Order, OrderItem
from django.utils.html import format_html

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug','image_tag')
    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height:50px;" />', obj.image.url)
        return "-"
    image_tag.short_description = 'Image'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'category', 'price', 'stock', 'created_at', 'image_tag')
    
    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height:50px;" />', obj.image.url)
        return "-"
    image_tag.short_description = 'Image'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'email', 'is_paid', 'created_at')
    list_filter = ('is_paid', 'created_at')
    
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'price', 'quantity')
