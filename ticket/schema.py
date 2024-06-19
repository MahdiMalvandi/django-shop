import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from utils.permissions import admin_required
from .models import *


# region object types
class ChatObjectType(DjangoObjectType):
    class Meta:
        model = Chat
        fields = '__all__'


class MessageObjectType(DjangoObjectType):
    class Meta:
        model = Message
        fields = '__all__'


# endregion object types

# region mutations
class CreateTicketMutation(graphene.Mutation):
    class Arguments:
        content = graphene.String(required=True)
        title = graphene.String(required=True)

    success = graphene.Boolean(default_value=False, required=False)
    chat = graphene.Field(ChatObjectType, required=False)

    @login_required
    def mutate(self, info, content, title):
        chat = Chat.objects.create(creator=info.context.user, title=title)
        message = Message.objects.create(user=info.context.user, content=content, chat=chat)
        return CreateTicketMutation(success=True, chat=chat)


class CloseTicketMutation(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean(default_value=False, required=False)

    @admin_required
    def mutate(self, info, id):
        try:
            chat = Chat.objects.get(id=id)
        except Chat.DoesNotExist:
            raise Exception('A chat with this data does not already exists')
        if not chat.is_open:
            raise Exception("The chat must be opened")
        chat.is_open = False
        chat.save()
        return CloseTicketMutation(success=True)


class CreateMessageMutation(graphene.Mutation):
    class Arguments:
        chat = graphene.Int(required=True)
        content = graphene.String(required=True)

    success = graphene.Boolean(default_value=False, required=False)
    message = graphene.Field(MessageObjectType, required=False)
    chat = graphene.Field(ChatObjectType, required=False)

    def mutate(self, info, chat, content):
        try:
            current_chat = Chat.objects.get(id=id)
        except Chat.DoesNotExist:
            raise Exception('A chat with this data does not already exists')
        user = info.context.user
        if not current_chat.is_open:
            raise Exception('the chat is closed')
        if not user.is_staff and not user == current_chat.creator:
            raise Exception("You must be an admin to reply to messages or you must be the creator of this chat")
        message = Message.objects.create(content=content, user=user, chat=current_chat)
        return CreateMessageMutation(message=message, success=True)


class OpenTicketMutation(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean(default_value=False, required=False)

    @admin_required
    def mutate(self, info, id):
        try:
            chat = Chat.objects.get(id=id)
        except Chat.DoesNotExist:
            raise Exception('A chat with this data does not already exists')
        if chat.is_open:
            raise Exception("The chat must be closed")
        chat.is_open = True
        chat.save()
        return OpenTicketMutation(success=True)


# endregion

class Query(graphene.ObjectType):
    chats = graphene.List(ChatObjectType)
    chat = graphene.Field(ChatObjectType, id=graphene.Int())

    def resolve_chats(self, info):
        if info.context.user.is_staff:
            return Chat.objects.select_related('creator').filter(is_open=True)
        else:
            return Chat.objects.select_related('creator').filter(creator=info.context.user)

    def resolve_chat(self, info, id):
        try:
            chat = Chat.objects.select_related('creator').get(id=id)
            return chat
        except Chat.DoesNotExist:
            Exception('There is no such chat with this id')


class Mutation(graphene.ObjectType):
    create_ticket = CreateTicketMutation.Field()
    close_ticket = CloseTicketMutation.Field()
    open_ticket = OpenTicketMutation.Field()
    create_message = CreateMessageMutation.Field()
