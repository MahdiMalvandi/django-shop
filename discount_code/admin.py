from django.contrib import admin
from .models import DiscountCode

@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'code', 'expiration_date', 'created', 'is_used', 'percent']