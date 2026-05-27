from decimal import Decimal
from .models import Product


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart', {})
        self.cart = cart

    def add(self, product, quantity=1, update_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}

        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        products = Product.objects.filter(id__in=self.cart.keys())
        products_dict = {str(p.id): p for p in products}
        for pid, item in self.cart.items():
            product = products_dict.get(pid)
            if product:
                item_copy = item.copy()
                item_copy['product'] = product
                item_copy['price'] = Decimal(item['price'])
                item_copy['total_price'] = item_copy['price'] * item['quantity']
                yield item_copy

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        self.session['cart'] = {}
        self.save()