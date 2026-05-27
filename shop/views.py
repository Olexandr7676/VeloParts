from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import transaction

from .models import Product, Category, Order, OrderItem, Profile, Newsletter
from .forms import ReviewForm, NewsletterForm, SignUpForm, OrderForm, ProfileForm
from .cart import Cart


def base_context():
    return {'categories': Category.objects.all()}


def home_view(request, category_id=None):
    ctx = base_context()
    if category_id:
        current_category = get_object_or_404(Category, id=category_id)
        products_list = Product.objects.filter(category=current_category).order_by('-created_at')
        ctx['current_category'] = current_category
    else:
        products_list = Product.objects.all().order_by('-created_at')

    paginator = Paginator(products_list, 9)
    ctx['products'] = paginator.get_page(request.GET.get('page'))
    return render(request, 'shop/index.html', ctx)


def product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Обробка форми відгуків
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
            messages.success(request, 'Відгук додано!')
            return redirect('product', product_id=product.id)
    else:
        form = ReviewForm()

    ctx = base_context()
    ctx.update({
        'product': product,
        'reviews': product.reviews.all().order_by('-created_at'),
        'form': form,
        'avg_rating': product.get_avg_rating(),
    })
    return render(request, 'shop/product.html', ctx)


def cart_view(request):
    ctx = base_context()
    ctx.update({'cart': Cart(request)})
    return render(request, 'shop/cart.html', ctx)


@require_POST
def add_to_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product=product, quantity=quantity)
    messages.success(request, f'Товар "{product.name}" додано до кошика!')
    return redirect('cart')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, 'Товар видалено з кошика.')
    return redirect('cart')


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = max(1, int(request.POST.get('quantity', 1)))
    cart.add(product=product, quantity=quantity, update_quantity=True)
    return redirect('cart')


@login_required
@transaction.atomic
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Ваш кошик порожній.")
        return redirect('cart')

    profile, _ = Profile.objects.get_or_create(user=request.user)

    # Обробка створення замовлення
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            total = cart.get_total_price()

            # Бонуси
            if form.cleaned_data.get('use_bonuses') and profile.bonuses > 0:
                discount = min(profile.bonuses, total)
                total -= float(discount)
                profile.bonuses -= discount
                profile.save()

            order = Order.objects.create(
                user=request.user, total_price=total,
                last_name=form.cleaned_data['last_name'],
                first_name=form.cleaned_data['first_name'],
                phone=form.cleaned_data['phone'],
                city=form.cleaned_data.get('city', ''),
                warehouse=form.cleaned_data.get('warehouse', '')
            )
            for item in cart:
                OrderItem.objects.create(
                    order=order, product=item['product'],
                    quantity=item['quantity'], price=item['price']
                )
            cart.clear()
            messages.success(request, 'Замовлення успішно оформлено!')
            return redirect('cabinet')
    else:
        form = OrderForm(initial={
            'last_name': profile.last_name,
            'first_name': profile.first_name,
            'phone': profile.phone
        })

    ctx = base_context()
    ctx.update({'cart': cart, 'form': form})
    return render(request, 'shop/checkout.html', ctx)


@login_required
def cabinet(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    # Збереження профілю
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Дані збережено!')
            return redirect('cabinet')
    else:
        form = ProfileForm(instance=profile)

    # --- ВИПРАВЛЕНА ЛОГІКА ЗАМОВЛЕНЬ ---
    current_status_filter = request.GET.get('status')

    if request.user.is_staff:
        # Якщо це АДМІН — показуємо всі замовлення сайту
        orders_list = Order.objects.all().order_by('-created_at')

        # Якщо адмін натиснув на фільтр (напр. "Нові")
        if current_status_filter:
            orders_list = orders_list.filter(status=current_status_filter)
    else:
        # Якщо це звичайний КЛІЄНТ — показуємо тільки його особисті замовлення
        orders_list = Order.objects.filter(user=request.user).order_by('-created_at')

    # Вмикаємо пагінацію (по 10 замовлень на сторінку)
    paginator = Paginator(orders_list, 10)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)

    ctx = base_context()
    ctx.update({
        'orders': orders,
        'profile': profile,
        'profile_form': form,
        'current_status_filter': current_status_filter  # Передаємо в шаблон, щоб кнопки підсвічувались
    })
    return render(request, 'shop/cabinet.html', ctx)
def signup(request):
    # Обробка реєстрації
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, 'Реєстрація успішна!')
            return redirect('home')
    else:
        form = SignUpForm()

    ctx = base_context()
    ctx.update({'form': form})
    return render(request, 'shop/signup.html', ctx)


@login_required
@require_POST
def order_change_status(request, order_id):
    if not request.user.is_staff:
        return redirect('home')
    order = get_object_or_404(Order, id=order_id)
    order.status = request.POST.get('status')
    order.save()
    messages.success(request, 'Статус замовлення змінено.')
    return redirect(request.META.get('HTTP_REFERER', 'cabinet'))


def subscribe_view(request):
    email = request.POST.get('email')
    if email:
        Newsletter.objects.get_or_create(email=email)
        messages.success(request, 'Підписку оформлено!')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def about_view(request): return render(request, 'shop/about.html', base_context())


def how_to_order_view(request): return render(request, 'shop/how_to_order.html', base_context())


def payment_view(request): return render(request, 'shop/payment.html', base_context())


def contacts_view(request): return render(request, 'shop/contacts.html', base_context())