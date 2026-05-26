from django.contrib import admin
from django.core.mail import send_mass_mail
from django.conf import settings
from .models import (
    Category, Brand, Product, Review, Newsletter, NewsletterCampaign,
    Profile, Order, OrderItem
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'final_icon', 'name', 'parent', 'created_at', 'updated_at')
    list_display_links = ('id', 'name')
    search_fields = ('name',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = Category.objects.filter(parent__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'brand', 'price', 'created_at', 'updated_at')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'description')
    list_filter = ('category', 'brand')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('author', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'product')
    search_fields = ('author', 'text')
    readonly_fields = ('created_at',)


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at', 'is_active')
    search_fields = ('email',)
    list_filter = ('is_active',)
    readonly_fields = ('created_at',)


@admin.register(NewsletterCampaign)
class NewsletterCampaignAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created_at', 'sent')
    readonly_fields = ('sent', 'created_at')

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        if is_new and not obj.sent:
            subscribers = Newsletter.objects.filter(is_active=True).values_list('email', flat=True)
            if subscribers:
                official_message = f"""Вітаємо від магазину VeloParts 🚲

{obj.message}

---
З повагою,
Магазин VeloParts
📞 0 (99) 646-18-61
📍 м. Луцьк, вул. Соборності, 14
"""
                messages_to_send = tuple(
                    (obj.subject, official_message, settings.DEFAULT_FROM_EMAIL, [email])
                    for email in subscribers
                )
                try:
                    send_mass_mail(messages_to_send, fail_silently=False)
                    obj.sent = True
                    obj.save()
                except Exception as e:
                    print(f"Помилка розсилки: {e}")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'bonuses')
    search_fields = ('user__username', 'phone')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'city', 'created_at')
    list_filter = ('status', 'created_at')
    list_editable = ('status',)
    search_fields = ('user__username', 'city')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')