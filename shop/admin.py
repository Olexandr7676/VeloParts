from django.contrib import admin
from .models import Category, Brand, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # Виводимо колонки в адмінці
    list_display = ('name', 'created_at', 'updated_at')

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Тут виводимо навіть більше: до якого бренду і категорії належить товар
    list_display = ('name', 'category', 'brand', 'price', 'created_at', 'updated_at')