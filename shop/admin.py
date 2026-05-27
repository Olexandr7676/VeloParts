from django.contrib import admin
from django.core.mail import send_mass_mail
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
    list_display = ('id', 'name', 'icon', 'created_at')


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'brand', 'price', 'created_at')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'product')
    search_fields = ('user__username', 'text')


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at')


@admin.register(NewsletterCampaign)
class NewsletterCampaignAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created_at', 'sent')
    readonly_fields = ('sent', 'created_at')

    # Додаємо дію для відправки листів
    actions = ['send_newsletter']

    def send_newsletter(self, request, queryset):
        emails = list(Newsletter.objects.values_list('email', flat=True))
        if not emails:
            self.message_user(request, "Немає підписників для відправки!")
            return

        messages = []
        for campaign in queryset:
            if not campaign.sent:
                # Зверни увагу: переконайся, що в моделі NewsletterCampaign є поле 'content'
                # Якщо воно називається інакше, виправ на потрібну назву
                messages.append((campaign.subject, campaign.content, 'kriskolok2@gmail.com', emails))
                campaign.sent = True
                campaign.save()

        if messages:
            send_mass_mail(messages, fail_silently=False)
            self.message_user(request, f"Розсилка успішно відправлена на {len(emails)} адрес!")
        else:
            self.message_user(request, "Ця розсилка вже була відправлена.")

    send_newsletter.short_description = "Відправити вибрану розсилку"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'bonuses')
    search_fields = ('user__username', 'phone')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'city', 'created_at')
    list_filter = ('status', 'created_at')
    list_editable = ('status',)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')