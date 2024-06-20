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
        address = graphene.String(required=True)
        postal_code = graphene.String(required=True)
        province = graphene.String(required=True)
        city = graphene.String(required=True)

    order = graphene.Field(OrderObjectType, required=False)
    success = graphene.Boolean(required=False, default_value=False)


    def mutate(self, info, address, postal_code, province, city):
        # get user
        user = info.context.user

        # get user cart from Cart class
        cart = Cart(info.context.session)

        # create order
        if len(cart) > 0:
            order = Order.objects.create(user=user, address=address, postal_code=postal_code, province=province, city=city)

            # create order items
            for item in cart:
                if item['quantity'] > 0:
                    OrderItem.objects.create(order=order, product=item['product'], price=item['new_price'],
                                             quantity=item["quantity"])
                    cart.clear()
        else:
            raise Exception('There is no products in cart')
        info.context.session['order_id'] = order.id
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
