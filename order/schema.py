import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from .models import *
from cart.cart import Cart


# region object types
class OrderObjectType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"


class OrderItemObjectType(DjangoObjectType):
    class Meta:
        model = OrderItem
        fields = "__all__"


# endregion

# region mutations
class CreateOrderMutation(graphene.Mutation):
    class Arguments:
        address = graphene.String(required=False)
        postal_code = graphene.String(required=False)
        province = graphene.String(required=False)
        city = graphene.String(required=False)

    order = graphene.Field(OrderObjectType, required=False)
    success = graphene.Boolean(required=False, default_value=False)

    def mutate(self, info, address=None, postal_code=None, province=None, city=None):
        # get user
        user = info.context.user

        # get user cart from Cart class
        cart = Cart(info.context.session)

        user_changed = False
        # validate address
        if address is None and user.address is None:
            raise Exception("Please provide address")
        else:
            if address:
                order_address = address
                if not user.address:
                    user.address = order_address
                    user_changed = True

            if user.address:
                order_address = user.address

        # validate city
        if city is None and user.city is None:
            raise Exception("Please provide city")
        else:
            if city:
                order_city = city
                if not user.city:
                    user.city = order_city
                    user_changed = True
            if user.city:
                order_city = user.city

        # validate province
        if province is None and user.province is None:
            raise Exception("Please provide province")
        else:
            if province:
                order_province = province
                if not user.province:
                    user.province = order_province
                    user_changed = True
            if user.province:
                order_province = user.province

        # validate postal code
        if postal_code is None and user.postal_code is None:
            raise Exception("Please provide postal code")
        else:
            if postal_code:
                order_postal_code = postal_code
                if not user.postal_code:
                    user.postal_code = order_postal_code
                    user_changed = True
            if user.postal_code:
                order_postal_code = user.postal_code

        # create order
        if len(cart) > 0:
            order = Order.objects.create(user=user, address=order_address, postal_code=order_postal_code,
                                         province=order_province,
                                         city=order_city, price=cart.get_total_price())

            # create order items
            for item in cart:
                if not item['product'].is_salable:
                    raise Exception('product is not a salable product')
                if item['quantity'] > 0:
                    OrderItem.objects.create(order=order, product=item['product'], price=item['new_price'],
                                             quantity=item["quantity"])
                    cart.clear()
        else:
            raise Exception('There is no products in cart')
        info.context.session['order_id'] = order.id
        if user_changed:
            user.save()
        return CreateOrderMutation(order=order, success=True)


# endregion mutations

class Query(graphene.ObjectType):
    orders = graphene.List(OrderObjectType)
    order = graphene.Field(OrderObjectType, id=graphene.Int())

    def resolve_orders(self, info):
        # get user
        user = info.context.user

        # get user orders
        orders = Order.objects.filter(user=user)
        return orders

    def resolve_order(self, info, id: int):
        # get order object
        try:
            order = Order.objects.get(id=id)
        except Order.DoesNotExist:
            raise Exception("Order does not exist")
        return order


class Mutation(graphene.ObjectType):
    create_order = CreateOrderMutation.Field()
