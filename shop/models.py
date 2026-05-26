from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.contrib.auth.models import User
from decimal import Decimal


# --- КАТЕГОРІЇ ---
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва категорії")
    icon = models.CharField(max_length=10, verbose_name="Іконка (емоджі)", blank=True, null=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='subcategories',
        verbose_name="Батьківська категорія"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено о")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено о")

    @property
    def final_icon(self):
        return self.icon or "⚙️"

    def __str__(self):
        return f"{self.parent.name} → {self.name}" if self.parent else self.name

    def clean(self):
        if self.parent and self.parent.parent:
            raise ValidationError("Не можна створювати під-під-категорії.")
        if self.parent == self:
            raise ValidationError("Категорія не може бути батьківською для самої себе.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"


# --- БРЕНДИ ---
class Brand(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва бренду")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено о")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено о")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Бренд"
        verbose_name_plural = "Бренди"


# --- ТОВАРИ ---
class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Назва товару")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    description = models.TextField(verbose_name="Опис товару", blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Фото")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категорія")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name="Бренд", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено о")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено о")

    def __str__(self):
        return self.name

    def get_avg_rating(self):
        result = self.reviews.aggregate(avg=Avg('rating'))
        return round(result['avg'], 1) if result['avg'] else 0

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товари"


# --- ПРОФІЛЬ КОРИСТУВАЧА ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Бонуси")
    first_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Ім'я")
    last_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Прізвище")
    middle_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="По батькові")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Місто")
    warehouse = models.CharField(max_length=255, blank=True, null=True, verbose_name="Відділення НП")

    def __str__(self):
        return f"Профіль: {self.user.username}"

    class Meta:
        verbose_name = "Профіль"
        verbose_name_plural = "Профілі"


# --- ЗАМОВЛЕННЯ ---
class Order(models.Model):
    STATUS_CHOICES = [('new', 'Нове'), ('sent', 'Відправлено'), ('done', 'Виконано')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Користувач")
    last_name = models.CharField(max_length=50, verbose_name="Прізвище")
    first_name = models.CharField(max_length=50, verbose_name="Ім'я")
    middle_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="По батькові")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    city = models.CharField(max_length=100, verbose_name="Місто")
    warehouse = models.CharField(max_length=255, verbose_name="Відділення")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Загальна сума")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    bonuses_awarded = models.BooleanField(default=False, verbose_name="Бонуси нараховано")

    def save(self, *args, **kwargs):
        if self.status == 'done' and not self.bonuses_awarded:
            bonus_amount = self.total_price * Decimal('0.05')
            self.user.profile.bonuses += bonus_amount
            self.user.profile.save()
            self.bonuses_awarded = True
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"


# --- ТОВАРИ У ЗАМОВЛЕННІ ---
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Замовлення")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Кількість")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна продажу")

    def get_total_price(self):
        return self.price * self.quantity

    class Meta:
        verbose_name = "Товар у замовленні"
        verbose_name_plural = "Товари у замовленні"


# --- ВІДГУКИ ---
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Товар")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Користувач")
    author = models.CharField(max_length=100, verbose_name="Автор відгуку")
    text = models.TextField(verbose_name="Текст")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оцінка (1–5)"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено о")

    class Meta:
        verbose_name = "Відгук"
        verbose_name_plural = "Відгуки"

    def __str__(self):
        return f"{self.author} — {self.product.name}"


# --- РОЗСИЛКА ---
class Newsletter(models.Model):
    email = models.EmailField(unique=True, verbose_name="Email підписника")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата підписки")
    is_active = models.BooleanField(default=True, verbose_name="Активна підписка")

    class Meta:
        verbose_name = "Підписник"
        verbose_name_plural = "Підписники (Розсилка)"

    def __str__(self):
        return self.email


class NewsletterCampaign(models.Model):
    subject = models.CharField(max_length=255, verbose_name="Тема листа")
    message = models.TextField(verbose_name="Текст листа")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    sent = models.BooleanField(default=False, verbose_name="Відправлено")

    class Meta:
        verbose_name = "Масова розсилка"
        verbose_name_plural = "Масові розсилки"

    def __str__(self):
        return self.subject