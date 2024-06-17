import random
import string

from django.db import models
from user.models import User


class DiscountCode(models.Model):
    code = models.CharField(max_length=50, blank=True, null=True)
    user = models.ForeignKey(User, related_name='discount_codes_created', on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField()
    percent = models.PositiveIntegerField()
    is_used = models.BooleanField(default=False)



    def save(
        self, *args, **kwargs
    ):
        if self.code is None:
            allowed_chars = ''.join((string.ascii_letters, string.digits))
            code = ''.join(random.choice(allowed_chars) for _ in range(10))
            self.code = code
        super(DiscountCode, self).save(*args, **kwargs)