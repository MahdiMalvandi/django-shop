import graphene
from product.models import Product
from .cart import Cart
from product.schema import ProductType


def show_cart(user_cart):
    products_info = []
    product_ids = user_cart.cart.keys()
    products = Product.objects.filter(id__in=product_ids)
    for product in products:
        item = user_cart.cart[str(product.id)]
        products_info.append(CartProductType(
            product=product,
            quantity=item['quantity'],
            new_price=item['new_price'],
        ))
    total_quantity = sum(item['quantity'] for item in user_cart.cart.values())
    total_price = user_cart.get_total_price()
    cart_info = CartInfoType(
        cart=products_info,
        total_quantity=total_quantity,
        total_price=total_price
    )
    return cart_info


# region object type

class CartProductType(graphene.ObjectType):
    product = graphene.Field(ProductType)
    quantity = graphene.Int()
    new_price = graphene.Float()


class CartInfoType(graphene.ObjectType):
    cart = graphene.List(CartProductType)
    total_quantity = graphene.Int()
    total_price = graphene.Float()


# endregion object type

# region mutations
class AddProductToCartMutation(graphene.Mutation):
    class Arguments:
        product_slug = graphene.String(required=True)

    cart_data = graphene.Field(CartInfoType)
    success = graphene.Boolean(default_value=False)

    @staticmethod
    def mutate(root, info, product_slug):
        product = Product.objects.get(slug=product_slug)
        user_cart = Cart(info.context.session)
        user_cart.add(product)
        return AddProductToCartMutation(cart_data=show_cart(user_cart), success=True)


class RemoveProductFromCartMutation(graphene.Mutation):
    class Arguments:
        product_slug = graphene.String(required=True)

    cart_data = graphene.Field(CartInfoType)
    success = graphene.Boolean(default_value=False)

    @staticmethod
    def mutate(root, info, product_slug):
        product = Product.objects.get(slug=product_slug)
        user_cart = Cart(info.context.session)
        user_cart.remove(product)
        return RemoveProductFromCartMutation(cart_data=show_cart(user_cart), success=True)


class DecreaseProductQuantityMutation(graphene.Mutation):
    class Arguments:
        product_slug = graphene.String(required=True)

    cart_data = graphene.Field(CartInfoType)
    success = graphene.Boolean(default_value=False)

    @staticmethod
    def mutate(root, info, product_slug):
        product = Product.objects.get(slug=product_slug)
        user_cart = Cart(info.context.session)
        user_cart.decrease(product)
        return DecreaseProductQuantityMutation(cart_data=show_cart(user_cart), success=True)


#
class ClearCartMutation(graphene.Mutation):
    cart_data = graphene.Field(CartInfoType, required=False)
    success = graphene.Boolean(default_value=False)

    @staticmethod
    def mutate(root, info):
        user_cart = Cart(info.context.session)
        user_cart.clear()
        return ClearCartMutation(cart_data=show_cart(user_cart), success=True)


# endregion mutations


class Query(graphene.ObjectType):
    cart_data = graphene.Field(CartInfoType)

    @staticmethod
    def resolve_cart_data(root, info):

        user_cart = Cart(info.context.session)
        return show_cart(user_cart)


class Mutation(graphene.ObjectType):
    add_product_to_cart = AddProductToCartMutation.Field()
    remove_product_from_cart = RemoveProductFromCartMutation.Field()
    decrease_product_quantity = DecreaseProductQuantityMutation.Field()
    clear_cart = ClearCartMutation.Field()
