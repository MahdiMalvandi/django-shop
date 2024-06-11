from graphql import GraphQLError
from functools import wraps


class PermissionDeniedError(GraphQLError):
    def __init__(self, message):
        super().__init__(message)
        self.extensions = {'code': 'FORBIDDEN', 'status': 403}


def admin_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        info = args[1]
        user = info.context.user
        if not user.is_authenticated or not user.is_staff:
            raise PermissionDeniedError("You do not have permission to perform this action")
        return func(*args, **kwargs)

    return wrapper
