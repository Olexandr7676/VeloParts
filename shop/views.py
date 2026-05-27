from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import transaction
from decimal import Decimal

from .models import Product, Category, Order, OrderItem, Profile
from .forms import ReviewForm, NewsletterForm, SignUpForm, OrderForm, ProfileForm
from .cart import Cart

# ── БАЗОВИЙ КОНТЕКСТ ────────────────────────────────────────────────────────
def base_context():
    return {'categories': Category.objects.all()}

# ── ГОЛОВНА / КАТЕГОРІЇ ────────────────────────────────────────────────────
def home_view(request, category_id=None):
    ctx = base_context()
    current_category = None
    if category_id:
        current_category = get_object_or_404(Category, id=category_id)
        products_list = Product.objects.filter(category=current_category).order_by('-created_at')
    else:
        products_list = Product.objects.all().order_by('-created_at')

    paginator = Paginator(products_list, 9)
    products = paginator.get_page(request.GET.get('page'))

    ctx.update({
        'products': products,
        'current_category': current_category,
        'page_title': f'{current_category.name} | VeloParts' if current_category else 'Головна | VeloParts',
    })
    return render(request, 'shop/index.html', ctx)

# ── ТОВАР ──────────────────────────────────────────────────────────────────
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

# ── КОШИК ──────────────────────────────────────────────────────────────────
def cart_view(request):
    ctx = base_context()
    ctx.update({'cart': Cart(request), 'page_title': 'Кошик | VeloParts'})
    return render(request, 'shop/cart.html', ctx)

@require_POST
def add_to_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product, quantity=int(request.POST.get('quantity', 1)))
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    cart.remove(get_object_or_404(Product, id=product_id))
    return redirect('cart')

@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    cart.add(product=get_object_or_404(Product, id=product_id),
             quantity=max(1, int(request.POST.get('quantity', 1))),
             update_quantity=True)
    return redirect('cart')

# ── ЗАМОВЛЕННЯ ─────────────────────────────────────────────────────────────
@login_required
@transaction.atomic
def checkout(request):
    cart = Cart(request)
    if not cart:
        messages.warning(request, "Ваш кошик порожній.")
        return redirect('cart')

    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            total = cart.get_total_price()
            if form.cleaned_data.get('use_bonuses') and profile.bonuses > 0:
                discount = min(profile.bonuses, total)
                total -= discount
                profile.bonuses -= discount
                profile.save()

            order = Order.objects.create(
                user=request.user,
                total_price=total,
                last_name=form.cleaned_data['last_name'],
                first_name=form.cleaned_data['first_name'],
                phone=form.cleaned_data['phone'],
                city=form.cleaned_data.get('city', ''),
                warehouse=form.cleaned_data.get('warehouse', '')
            )
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'],
                                         quantity=item['quantity'], price=item['price'])
            cart.clear()
            messages.success(request, f'🎉 Замовлення №{order.id} оформлено!')
            return redirect('cabinet')
    else:
        form = OrderForm(initial={'last_name': profile.last_name,
                                  'first_name': profile.first_name,
                                  'phone': profile.phone})

    ctx = base_context()
    ctx.update({'cart': cart, 'form': form, 'page_title': 'Оформлення | VeloParts'})
    return render(request, 'shop/checkout.html', ctx)

# ── КАБІНЕТ ────────────────────────────────────────────────────────────────
@login_required
def cabinet(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Дані збережено!')
            return redirect('cabinet')
    else:
        form = ProfileForm(instance=profile)

    ctx = base_context()
    ctx.update({
        'orders': Order.objects.filter(user=request.user).order_by('-created_at'),
        'profile': profile,
        'profile_form': form,
        'page_title': 'Кабінет | VeloParts'
    })
    return render(request, 'shop/cabinet.html', ctx)

# ── ІНШЕ ──────────────────────────────────────────────────────────────────
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'shop/signup.html', {**base_context(), 'form': form})

@login_required
@require_POST
def order_change_status(request, order_id):
    if not request.user.is_staff: return redirect('home')
    order = get_object_or_404(Order, id=order_id)
    order.status = request.POST.get('status')
    order.save()
    messages.success(request, f'Статус замовлення №{order.id} змінено.')
    return redirect(request.META.get('HTTP_REFERER', 'cabinet'))

def subscribe_view(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        from .models import Newsletter
        Newsletter.objects.get_or_create(email=form.cleaned_data['email'])
        messages.success(request, '✅ Підписку оформлено!')
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def about_view(request): return render(request, 'shop/about.html', {**base_context()})
def how_to_order_view(request): return render(request, 'shop/how_to_order.html', {**base_context()})
def payment_view(request): return render(request, 'shop/payment.html', {**base_context()})
def contacts_view(request): return render(request, 'shop/contacts.html', {**base_context()})