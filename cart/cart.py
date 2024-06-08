from functools import wraps

from product.models import Product


def product_exists(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        product = args[1]
        if str(product.id) in self.cart.keys():
            return func(*args, **kwargs)
        else:
            raise Exception('There is no such product in the shopping cart')

    return wrapper


class Cart:
    def __init__(self, session):
        self.session = session
        cart = self.session.get('cart')

        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product):

        product_id = str(product.id)

        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 1, 'new_price': product.new_price}
        else:
            if self.cart[product_id]['quantity'] < product.inventory:
                self.cart[product_id]['quantity'] += 1
        self.save()

    @product_exists
    def decrease(self, product):
        product_id = str(product.id)
        if self.cart[product_id]['quantity'] > 0:
            self.cart[product_id]['quantity'] -= 1
        else:
            self.remove(product)
        self.save()

    @product_exists
    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
        self.save()

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def save(self):
        print(self.cart)
        self.session.modified = True

    def clear(self):
        del self.session['cart']
        self.save()

    def get_total_price(self):
        priced = sum(item['new_price'] * item['quantity'] for item in self.cart.values())
        return priced

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart_dict = self.cart.copy()
        for product in products:
            cart_dict[str(product.id)]['product'] = product
        for item in cart_dict.values():
            yield item
