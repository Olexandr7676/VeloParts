from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.contrib.auth.models import User
from decimal import Decimal


# --- КАТЕГОРІЇ ---
class Category(models.Model):
    name = models.CharField(max_length=26, verbose_name="Назва категорії")
    icon = models.CharField(max_length=10, verbose_name="Іконка", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено о")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено о")

    def __str__(self): return self.name

    class Meta: verbose_name = "Категорія"; verbose_name_plural = "Категорії"


# --- БРЕНДИ ---
class Brand(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва бренду")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено о")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено о")

    def __str__(self): return self.name

    class Meta: verbose_name = "Бренд"; verbose_name_plural = "Бренди"


# --- ТОВАРИ ---
class Product(models.Model):
    name = models.CharField(max_length=26, verbose_name="Назва товару")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    description = models.TextField(verbose_name="Опис товару", blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Фото")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категорія")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name="Бренд", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено о")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено о")

    def __str__(self): return self.name

    def get_avg_rating(self):
        avg = self.reviews.aggregate(avg=Avg('rating'))['avg']
        return round(avg, 1) if avg else 0

    class Meta: verbose_name = "Товар"; verbose_name_plural = "Товари"


# --- ПРОФІЛЬ ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Бонуси")
    first_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Ім'я")
    last_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Прізвище")
    middle_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="По батькові")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Місто")
    warehouse = models.CharField(max_length=255, blank=True, null=True, verbose_name="Відділення")

    def __str__(self): return f"Профіль: {self.user.username}"

    class Meta: verbose_name = "Профіль"; verbose_name_plural = "Профілі"


# --- ЗАМОВЛЕННЯ ---
class Order(models.Model):
    STATUS_CHOICES = [('new', 'Нове'), ('sent', 'Відправлено'), ('done', 'Виконано')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Користувач")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сума")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    bonuses_awarded = models.BooleanField(default=False, verbose_name="Бонуси")

    last_name = models.CharField(max_length=50, verbose_name="Прізвище")
    first_name = models.CharField(max_length=50, verbose_name="Ім'я")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    city = models.CharField(max_length=100, verbose_name="Місто")
    warehouse = models.CharField(max_length=255, verbose_name="Відділення")

    def save(self, *args, **kwargs):
        if self.status == 'done' and not self.bonuses_awarded:
            self.user.profile.bonuses += self.total_price * Decimal('0.05')
            self.user.profile.save()
            self.bonuses_awarded = True
        super().save(*args, **kwargs)

    class Meta: verbose_name = "Замовлення"; verbose_name_plural = "Замовлення"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    author = models.CharField(max_length=100)
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)


class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)


class NewsletterCampaign(models.Model):
    subject = models.CharField(max_length=255)
    message = models.TextField()
    sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)