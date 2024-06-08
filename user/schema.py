import graphene
from graphql import GraphQLError
from graphene_django.types import DjangoObjectType
from .models import *


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'profile', 'date_joined', 'last_seen', 'date_of_birth', 'bio', 'is_staff', 'is_seller', 'is_superuser',]


class UserQuery(graphene.ObjectType):
    users = graphene.List(UserType)

    @staticmethod
    def resolve_users(root, info, **kwargs):
        return User.objects.all()


class UserRegisterMutation(graphene.Mutation):
    class Arguments:
        first_name = graphene.String()
        last_name = graphene.String()
        password = graphene.String()
        phone_number = graphene.String()

    user = graphene.Field(UserType)
    success = graphene.Boolean(default_value=False)

    def mutate(root, info, password, phone_number, first_name, last_name):
        try:
            User.objects.get(phone_number=phone_number)
            raise GraphQLError('A user with this information already exists')
        except User.DoesNotExist:
            user_instance = User.objects.create_user(phone_number=phone_number, password=password)
            user_instance.first_name = first_name
            user_instance.last_name = last_name
            success = True
            # send code to user
        return UserRegisterMutation(user=user_instance, success=success)


class UserLoginMutation(graphene.Mutation):
    class Arguments:
        phone_number = graphene.String(required=False)

    @staticmethod
    def mutate(root, info, phone_number):
        if phone_number is None:
            raise GraphQLError('You must provide a phone')
        try:
            user = User.objects.get(phone_number=phone_number)
            # send verification code to user's phone number
        except User.DoesNotExist:
            raise GraphQLError('There is no such user with this phone number')


class Mutation(graphene.ObjectType):
    register = UserRegisterMutation.Field()
