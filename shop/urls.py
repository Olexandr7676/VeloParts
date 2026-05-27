from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ── ГОЛОВНА ТА КАТЕГОРІЇ ─────────────────────────────────────
    path('', views.home_view, name='home'),
    path('category/<int:category_id>/', views.home_view, name='category'),
    path('product/<int:product_id>/', views.product_view, name='product'),

    # ── ПІДПИСКА ─────────────────────────────────────────────────
    path('subscribe/', views.subscribe_view, name='subscribe'),

    # ── КОШИК ────────────────────────────────────────────────────
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),

    # ── ОФОРМЛЕННЯ ЗАМОВЛЕННЯ ────────────────────────────────────
    path('checkout/', views.checkout, name='checkout'),

    # ── КАБІНЕТ ──────────────────────────────────────────────────
    path('cabinet/', views.cabinet, name='cabinet'),
    path('order/<int:order_id>/status/', views.order_change_status, name='order_change_status'),

    # ── РЕЄСТРАЦІЯ ТА ВХІД ───────────────────────────────────────
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='shop/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # ── ВІДНОВЛЕННЯ ПАРОЛЯ ───────────────────────────────────────
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='shop/password_reset.html',
        email_template_name='shop/password_reset_email.html',
        subject_template_name='shop/password_reset_subject.txt',
    ), name='password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='shop/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='shop/password_reset_confirm.html'
    ), name='password_reset_confirm'),

    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='shop/password_reset_complete.html'
    ), name='password_reset_complete'),

    # ── СТАТИЧНІ СТОРІНКИ ────────────────────────────────────────
    path('about/', views.about_view, name='about'),
    path('how-to-order/', views.how_to_order_view, name='how_to_order'),
    path('payment/', views.payment_view, name='payment'),
    path('contacts/', views.contacts_view, name='contacts'),

]