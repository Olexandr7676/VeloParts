from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal

from .models import Product, Category, Brand, Review, Newsletter, Order, OrderItem, Profile
from .forms import ReviewForm, NewsletterForm, SignUpForm, OrderForm, ProfileForm
from .cart import Cart


def base_context():
    """Базовий контекст для всіх сторінок."""
    return {
        'categories': Category.objects.filter(parent=None).prefetch_related('subcategories'),
    }


# ─── ГОЛОВНА / КАТЕГОРІЇ ────────────────────────────────────────────────────
def home_view(request, category_id=None):
    ctx = base_context()
    current_category = None

    if category_id:
        current_category = get_object_or_404(Category, id=category_id)
        cats = [current_category] + list(current_category.subcategories.all())
        products_list = Product.objects.filter(category__in=cats).order_by('-created_at')
    else:
        products_list = Product.objects.all().order_by('-created_at')

    paginator = Paginator(products_list, 9)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    ctx.update({
        'products': products,
        'current_category': current_category,
        'page_title': f'{current_category.name} | VeloParts' if current_category else 'Головна | VeloParts',
    })
    return render(request, 'shop/index.html', ctx)


# ─── СТОРІНКА ТОВАРУ ────────────────────────────────────────────────────────
def product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Увійдіть, щоб залишити відгук.')
            return redirect('login')
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Відгук додано! 🚲')
            return redirect('product', product_id=product.id)
    else:
        form = ReviewForm()

    ctx = base_context()
    ctx.update({
        'product': product,
        'reviews': product.reviews.all().order_by('-created_at'),
        'form': form,
        'avg_rating': product.get_avg_rating(),
        'page_title': f'{product.name} | VeloParts',
    })
    return render(request, 'shop/product.html', ctx)


# ─── ПІДПИСКА ────────────────────────────────────────────────────────────────
@require_POST
def subscribe_view(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email']
        obj, created = Newsletter.objects.get_or_create(email=email)
        if created:
            try:
                send_mail(
                    '🚲 Вітаємо в VeloParts! Підписка оформлена',
                    f'Ви підписалися на новини магазину VeloParts!\n\nТепер ви першими дізнаєтесь про нові товари та акції.\n\n— Команда VeloParts',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=True
                )
                messages.success(request, '✅ Підписку оформлено!')
            except Exception:
                messages.success(request, '✅ Підписку оформлено!')
        else:
            messages.info(request, '📬 Цей email вже підписано.')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# ─── КОШИК ───────────────────────────────────────────────────────────────────
@require_POST
def add_to_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product=product, quantity=quantity)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'cart_length': len(cart), 'product_name': product.name})

    messages.success(request, f'"{product.name}" додано у кошик! 🛒')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart')


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        quantity = 1
    cart.add(product=product, quantity=quantity, update_quantity=True)
    return redirect('cart')


def cart_view(request):
    ctx = base_context()
    ctx['cart'] = Cart(request)
    ctx['page_title'] = 'Кошик | VeloParts'
    return render(request, 'shop/cart.html', ctx)


# ─── ОФОРМЛЕННЯ ЗАМОВЛЕННЯ ────────────────────────────────────────────────────
@login_required
@transaction.atomic
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Ваш кошик порожній.")
        return redirect('cart')

    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            total = cart.get_total_price()

            if form.cleaned_data.get('use_bonuses') and profile.bonuses > 0:
                if profile.bonuses >= total:
                    profile.bonuses -= total
                    total = Decimal('0.00')
                else:
                    total -= profile.bonuses
                    profile.bonuses = Decimal('0.00')
                profile.save()

            order = Order.objects.create(
                user=request.user,
                total_price=total,
                last_name=form.cleaned_data['last_name'],
                first_name=form.cleaned_data['first_name'],
                middle_name=form.cleaned_data.get('middle_name', ''),
                phone=form.cleaned_data['phone'],
                city=request.POST.get('city', ''),
                warehouse=request.POST.get('warehouse', '')
            )

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['price']
                )

            profile.phone = form.cleaned_data['phone']
            profile.last_name = form.cleaned_data['last_name']
            profile.first_name = form.cleaned_data['first_name']
            profile.save()

            cart.clear()
            messages.success(request, f'🎉 Замовлення №{order.id} успішно оформлено!')
            return redirect('cabinet')
    else:
        initial_data = {
            'last_name': profile.last_name or request.user.last_name,
            'first_name': profile.first_name or request.user.first_name,
            'middle_name': profile.middle_name,
            'phone': profile.phone,
        }
        form = OrderForm(initial=initial_data)

    ctx = base_context()
    ctx.update({'cart': cart, 'form': form, 'profile': profile, 'page_title': 'Оформлення | VeloParts'})
    return render(request, 'shop/checkout.html', ctx)


# ─── КАБІНЕТ ─────────────────────────────────────────────────────────────────
@login_required
def cabinet(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Ваші дані збережено!')
            return redirect('cabinet')
    else:
        profile_form = ProfileForm(instance=profile)

    status_filter = request.GET.get('status')

    if request.user.is_staff:
        orders_list = Order.objects.all().prefetch_related('items__product')
    else:
        orders_list = Order.objects.filter(user=request.user).prefetch_related('items__product')

    if status_filter in ['new', 'sent', 'done']:
        orders_list = orders_list.filter(status=status_filter)

    orders_list = orders_list.order_by('-created_at')

    paginator = Paginator(orders_list, 5)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)

    ctx = base_context()
    ctx.update({
        'orders': orders,
        'profile': profile,
        'profile_form': profile_form,
        'current_status_filter': status_filter,
        'page_title': 'Кабінет | VeloParts',
    })
    return render(request, 'shop/cabinet.html', ctx)


@login_required
@require_POST
def order_change_status(request, order_id):
    if not request.user.is_staff:
        return redirect('home')

    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    just_awarded = (new_status == 'done' and not order.bonuses_awarded)

    order.status = new_status
    order.save()

    if just_awarded:
        earned = order.total_price * Decimal('0.05')
        messages.success(request, f'Замовлення №{order.id} виконано! Нараховано кешбек: {earned:.2f} ₴ 🎁')
    else:
        messages.success(request, f'Статус замовлення №{order.id} змінено.')

    return redirect(request.META.get('HTTP_REFERER', 'cabinet'))


# ─── РЕЄСТРАЦІЯ ───────────────────────────────────────────────────────────────
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, '🎉 Акаунт створено! Ласкаво просимо!')
            return redirect('home')
    else:
        form = SignUpForm()

    ctx = base_context()
    ctx['form'] = form
    return render(request, 'shop/signup.html', ctx)


# ─── СТАТИЧНІ СТОРІНКИ ────────────────────────────────────────────────────────
def about_view(request):
    return render(request, 'shop/about.html', {**base_context(), 'page_title': 'Про нас | VeloParts'})