import graphene
from graphene_django.types import DjangoObjectType
from .models import *


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = '__all__'


class UserQuery(graphene.ObjectType):
    users = graphene.List(UserType)

    @staticmethod
    def resolve_users(root, info, **kwargs):
        return User.objects.all()


class UserRegisterMutation(graphene.Mutation):
    class Arguments:
        username = graphene.String()
        email = graphene.String()
        first_name = graphene.String()
        last_name = graphene.String()
        password = graphene.String()
        phone_number = graphene.String()

    user = graphene.Field(UserType)
    ok = graphene.Boolean(default_value=False)

    def mutate(root, info, username, email, password, phone_number, first_name, last_name):
        user_instance = User.objects.create_user(username=username, password=password, email=email)
        user_instance.first_name = first_name
        user_instance.last_name = last_name
        user_instance.phone_number = phone_number
        ok = True
        return UserRegisterMutation(user=user_instance, ok=ok)



class Mutation(graphene.ObjectType):
    register = UserRegisterMutation.Field()