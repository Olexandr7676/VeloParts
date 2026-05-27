from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.contrib.auth.models import User
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=26, verbose_name="Назва категорії")
    icon = models.CharField(max_length=10, verbose_name="Іконка", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено о")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено о") # Додано для адмінки

    def __str__(self): return self.name
    class Meta: verbose_name = "Категорія"; verbose_name_plural = "Категорії"

class Brand(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва бренду")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено о")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено о")
    def __str__(self): return self.name
    class Meta: verbose_name = "Бренд"; verbose_name_plural = "Бренди"

class Product(models.Model):
    name = models.CharField(max_length=50, verbose_name="Назва товару")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    description = models.TextField(verbose_name="Опис товару", blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Фото")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категорія")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено о")

    def get_avg_rating(self):
        avg = self.reviews.aggregate(avg=Avg('rating'))['avg']
        return round(avg, 1) if avg else 0

    def __str__(self): return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    first_name = models.CharField(max_length=50, blank=True, null=True) # Додали null=True
    last_name = models.CharField(max_length=50, blank=True, null=True)  # Додали null=True
    middle_name = models.CharField(max_length=50, blank=True, null=True) # Додали null=True
    phone = models.CharField(max_length=20, blank=True, null=True)      # Додали null=True
    city = models.CharField(max_length=100, blank=True, null=True)      # Додали null=True
    warehouse = models.CharField(max_length=255, blank=True, null=True) # Додали null=True

    def __str__(self): return self.user.username
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=[('new', 'Нове'), ('done', 'Виконано')], default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    bonuses_awarded = models.BooleanField(default=False)
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    warehouse = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if self.status == 'done' and not self.bonuses_awarded:
            self.user.profile.bonuses += self.total_price * Decimal('0.05')
            self.user.profile.save()
            self.bonuses_awarded = True
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)

class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

class NewsletterCampaign(models.Model):
    subject = models.CharField(max_length=255, verbose_name="Тема листа")
    message = models.TextField(verbose_name="Повід.")
    sent = models.BooleanField(default=False, verbose_name="Відправлено")
    created_at = models.DateTimeField(auto_now_add=True, null=True, verbose_name="Створено")

    def __str__(self): return self.subject
    class Meta: verbose_name = "Розсилка"; verbose_name_plural = "Розсилки"