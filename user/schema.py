import graphene
import graphql_jwt
from graphql import GraphQLError
from graphene_django.types import DjangoObjectType
from .models import *
from django.core.cache import cache

from .utils import send_code, check_verification_code
from graphql_jwt.shortcuts import get_token


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'profile', 'email', 'date_joined', 'last_seen',
                  'date_of_birth', 'bio', 'is_staff', 'is_seller', 'is_superuser', ]


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
        email = graphene.String(required=False)

    user = graphene.Field(UserType)
    success = graphene.Boolean(default_value=False)

    def mutate(root, info, password, phone_number, first_name, last_name, email=None):
        try:
            User.objects.get(phone_number=phone_number)
            raise GraphQLError('A user with this information already exists')
        except User.DoesNotExist:
            user_instance = User.objects.create_user(phone_number=phone_number, password=password)
            user_instance.first_name = first_name
            user_instance.last_name = last_name
            user_instance.email = email
            success = True
            # send code to user
        return UserRegisterMutation(user=user_instance, success=success)


class UserLoginMutation(graphene.Mutation):
    class Arguments:
        phone_number = graphene.String(required=False)
        email = graphene.String(required=False)
        password = graphene.String(required=False)

    message = graphene.String(required=False, default_value=None)
    error = graphene.String(required=False, default_value=None)
    email = graphene.String(required=False, default_value=None)
    token = graphene.String(required=False, default_value=None)


    @staticmethod
    def mutate(root, info, phone_number=None, email=None, password=None):
        send, where = False, None
        if phone_number:
            send, where = True, 'sms'
            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                raise GraphQLError('There is no such user with this phone number')
        elif email:
            send, where = True, 'email'
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise GraphQLError('There is no such user with this email address')
        else:
            raise GraphQLError('You must provide a phone or an email address')
        if password is None:
            if send:
                if where == 'sms':
                    # send code to sms
                    pass
                elif where == 'email':
                    # send code to emai
                    cache_key = f'email_verification:{user.email}'
                    cached_code = cache.get(cache_key)
                    if cached_code:
                        return UserLoginMutation(error='Verification code already sent')
                    sending_code = send_code(user.email)
                    return UserLoginMutation(message=sending_code['message'], email=user.email)

        else:
            # login with password
            if user.check_password(password):
                # send jwt code
                token = get_token(user)  # Generate JWT token for the user
                return VerificationCodeMutation(token=token)
            else:
                raise GraphQLError('Password is incorrect')


class VerificationCodeMutation(graphene.Mutation):
    class Arguments:
        code = graphene.String(required=True)
        code_location = graphene.String(required=True)
        email = graphene.String(required=False)
        phone_number = graphene.String(required=False)

    token = graphene.String(required=True)

    def mutate(self, info, code, code_location, email=None, phone_number=None):
        if code_location == 'sms':
            # check code sms
            pass
        elif code_location == 'email':
            if email is None:
                raise GraphQLError('You must provide an email address')
            checking_code = check_verification_code({'code': code, 'email': email})
            if checking_code['result']:
                user = User.objects.get(email=email)
                token = get_token(user)  # Generate JWT token for the user
                return VerificationCodeMutation(token=token)
            else:
                raise GraphQLError(checking_code['error'])
        else:
            raise GraphQLError('codeLocation must be "email" or "sms"')


class Mutation(graphene.ObjectType):
    register = UserRegisterMutation.Field()
    login = UserLoginMutation.Field()
    verify_code = VerificationCodeMutation.Field()
    verify_token = graphql_jwt.relay.Verify.Field()
    refresh_token = graphql_jwt.relay.Refresh.Field()