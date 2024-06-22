import random
import string

from django.db.models import Sum
from django.db.models.functions import Now
from django.utils.timezone import now

import graphene
from graphql_jwt.decorators import login_required

from order.models import Order
from order.schema import OrderObjectType
from graphene_django.types import DjangoObjectType
from .models import DiscountCode
from utils.permissions import admin_required


class DiscountCodeType(DjangoObjectType):
    is_expired = graphene.Boolean()

    class Meta:
        model = DiscountCode
        fields = "__all__"

    def resolve_is_expired(self, info):
        if self.expiration_date < now():
            return True
        else:
            return False


class CreateDiscountCode(graphene.Mutation):
    class Arguments:
        percent = graphene.Int(required=True)
        expiration_date = graphene.DateTime(required=True)
        code = graphene.String(required=False)

    success = graphene.Boolean(required=False, default_value=False)
    code = graphene.Field(DiscountCodeType, required=False)

    @admin_required
    def mutate(self, info, percent, expiration_date, code=None):
        user = info.context.user
        if code is None:
            allowed_chars = ''.join((string.ascii_letters, string.digits))
            code = ''.join(random.choice(allowed_chars) for _ in range(10))
        obj = DiscountCode.objects.create(user=user, code=code, expiration_date=expiration_date)
        return CreateDiscountCode(code=obj, success=True)


class UpdateDiscountCode(graphene.Mutation):
    class Arguments:
        percent = graphene.Int(required=False)
        expiration_date = graphene.DateTime(required=False)
        id = graphene.Int(required=True)
        code = graphene.String(required=False)

    success = graphene.Boolean(required=False, default_value=False)
    code = graphene.Field(DiscountCodeType, required=False)

    @admin_required
    def mutate(self, info, id, percent=None, expiration_date=None, code=None):
        user = info.context.user
        obj = DiscountCode.objects.filter(id=id)
        if not obj.exists():
            raise Exception('A Code with this data does not already exists')
        obj = obj.first()
        obj.code = code if code is not None else obj.code
        obj.expiration_date = expiration_date if expiration_date is not None else obj.expiration_date
        obj.percent = percent if percent is not None else obj.percent
        obj.save()
        return UpdateDiscountCode(code=obj, success=True)


class DeleteDiscountCode(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean(required=False, default_value=False)

    @admin_required
    def mutate(self, info, id):
        obj = DiscountCode.objects.filter(id=id)
        if not obj.exists():
            raise Exception('A Code with this data does not already exists')
        obj.first().delete()
        return UpdateDiscountCode(success=True)


class ApplyDiscountCode(graphene.Mutation):
    class Arguments:
        code = graphene.String(required=True)

    success = graphene.Boolean(default_value=False, required=False)
    order = graphene.Field(OrderObjectType, required=False)

    @login_required
    def mutate(self, info, code):
        # getting order id from user session
        order_id = info.context.session.get('order_id')

        # getting order obj from order model
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            raise Exception('Order does not found')

        # getting discount code from model
        try:
            code_obj = DiscountCode.objects.get(code=code)
        except DiscountCode.DoesNotExist:
            raise Exception('Code doesnt exists')

        if code_obj.is_used:
            raise Exception('The code already has been used')

        if code_obj.expiration_date < now():
            raise Exception('The code is expired')

        # calculate new price
        new_price = order.price - ((code_obj.percent * order.price) // 100)

        code_obj.is_used = True
        order.price = new_price
        order.discount_code = code_obj.code

        code_obj.save()
        order.save()
        return ApplyDiscountCode(order=order, success=True)


class DeleteDiscountCodeFromOrder(graphene.Mutation):
    success = graphene.Boolean(default_value=False, required=False)
    order = graphene.Field(OrderObjectType, required=False)

    @login_required
    def mutate(self, info):
        # getting order id from user session
        order_id = info.context.session.get('order_id')

        # getting order obj from order model
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            raise Exception('Order does not found')

        if not order.discount_code:
            raise Exception('Unused code')

        # getting code obj from code model
        try:
            code_obj = DiscountCode.objects.get(code=order.discount_code)
        except DiscountCode.DoesNotExist:
            raise Exception('Discount code does not found')

        # calculate new price
        new_price = ((order.price * 100) // (100 - code_obj.percent))

        order.discount_code = None
        order.price = new_price
        code_obj.is_used = False
        code_obj.save()
        order.save()
        return DeleteDiscountCodeFromOrder(order=order, success=True)



class Query(graphene.ObjectType):
    codes = graphene.List(DiscountCodeType, only_unexpired=graphene.Boolean(required=False))
    code = graphene.Field(DiscountCodeType, id=graphene.Int())

    @admin_required
    def resolve_codes(self, info, only_unexpired=None):
        if only_unexpired:
            codes = DiscountCode.objects.filter(expiration_date__in=Now())
        else:
            codes = DiscountCode.objects.all().order_by('expiration_date')
        return codes

    @admin_required
    def resolve_code(self, info, id: int):
        code = DiscountCode.objects.filter(id=id)
        if not code.exists():
            raise Exception('A Code with this data does not already exists')
        return code


class Mutation(graphene.ObjectType):
    create_code = CreateDiscountCode.Field()
    update_code = UpdateDiscountCode.Field()
    delete_code = DeleteDiscountCode.Field()
    apply_code = ApplyDiscountCode.Field()
    delete_discount_code_from_order = DeleteDiscountCodeFromOrder.Field()
