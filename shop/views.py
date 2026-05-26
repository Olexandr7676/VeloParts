from django.shortcuts import render

def home_view(request):
    context = {
        'page_title': 'Головна | VeloParts',
        'text_content': 'Ласкаво просимо до магазину VeloParts! 🚲'
    }
    return render(request, 'shop/index.html', context)

def about_view(request):
    context = {
        'page_title': 'Про нас | VeloParts',
        'text_content': 'Ми продаємо надійні деталі для велосипедів з 2026 року.'
    }
    return render(request, 'shop/about.html', context)