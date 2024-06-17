import random
import string
from django.utils.timezone import now

import graphene

from graphene_django.types import DjangoObjectType
from .models import DiscountCode
from utils.permissions import admin_required


class DiscountCodeType(DjangoObjectType):
    is_expired = graphene.Boolean()

    class Meta:
        model = DiscountCode
        fields = "__all__"

    def resolve_is_expired(self, info):
        if self.expiration_date<now():
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


class Query(graphene.ObjectType):
    codes = graphene.List(DiscountCodeType, only_unexpired=graphene.Boolean(required=False))
    code = graphene.Field(DiscountCodeType, id=graphene.Int())

    @admin_required
    def resolve_codes(self, info, only_unexpired=None):
        if only_unexpired:
            codes = DiscountCode.objects.filter(expiration_date__in=datetime.Now())
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
