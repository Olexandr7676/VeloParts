from django.contrib import admin
from django.urls import path
from shop import views  # Підключаємо нашу логіку
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Стандартні посилання
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),

    # Нові посилання для Лаби 6 (Категорії та Сторінка товару)
    path('category/<int:category_id>/', views.category_view, name='category'),
    path('product/<int:product_id>/', views.product_view, name='product'),
]

# Цей шматок коду обов'язковий, щоб на сайті відображалися фотографії
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)