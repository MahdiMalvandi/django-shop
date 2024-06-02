from django.contrib.postgres.search import TrigramSimilarity
from django.db import models
from django.core import validators
from django.contrib.auth.models import AbstractBaseUser, UserManager, PermissionsMixin
from django.utils import timezone


def user_profile_upload_path(instance, filename):
    return f"profiles/{instance.username}/{filename}"


class User(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    Username, password and email are required. Other fields are optional.
    """

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.CharField(max_length=32, unique=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(unique=True, validators=[
        validators.RegexValidator(r'^989[0-3,9]\d{8}$', 'Enter a valid mobile number')
    ])
    profile = models.ImageField(upload_to=user_profile_upload_path, blank=True, null=True)
    date_joined = models.DateTimeField('date joined', default=timezone.now)
    last_seen = models.DateTimeField('last seen date', default=timezone.now)

    date_of_birth = models.DateTimeField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_seller = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'phone_number']

    objects = UserManager()

    class Meta:
        db_table = 'users'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def is_loggedin_user(self):
        """
        Returns True if user has actually logged in with valid credentials.
        """
        return self.phone_number is not None or self.email is not None


    @classmethod
    def search(cls, query):
        return cls.objects.annotate(
            similarity=TrigramSimilarity('username', query) +
                       TrigramSimilarity('first_name', query) +
                       TrigramSimilarity('last_name', query)
        ).filter(similarity__gt=0.1).order_by('-similarity')


