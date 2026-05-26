from django.shortcuts import render
from .models import Category, Product


def home_view(request):
    # Дістаємо всі категорії та товари з бази даних
    categories = Category.objects.all()
    products = Product.objects.all()

    context = {
        'page_title': 'Головна | VeloParts',
        'categories': categories,
        'products': products,
    }
    return render(request, 'shop/index.html', context)


def about_view(request):
    context = {
        'page_title': 'Про нас | VeloParts',
    }
    return render(request, 'shop/about.html', context)