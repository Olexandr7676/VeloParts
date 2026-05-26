from django.shortcuts import render, get_object_or_404
from .models import Category, Product

def home_view(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    return render(request, 'shop/index.html',
                  {'categories': categories, 'products': products, 'page_title': 'Головна | VeloParts'})

def about_view(request):
    return render(request, 'shop/about.html', {'page_title': 'Про нас | VeloParts'})

# Фільтрація по категорії
def category_view(request, category_id):
    categories = Category.objects.all()
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)  # Беремо товари ТІЛЬКИ цієї категорії

    return render(request, 'shop/index.html', {
        'categories': categories,
        'products': products,
        'page_title': f'{category.name} | VeloParts',
    })

# Сторінка одного товару
def product_view(request, product_id):
    categories = Category.objects.all()
    product = get_object_or_404(Product, id=product_id)

    return render(request, 'shop/product.html', {
        'categories': categories,
        'product': product,
        'page_title': f'{product.name} | VeloParts',
    })