from django.contrib import admin

from .models import *


# region Inlines
class ImageInline(admin.TabularInline):
    model = Image
    extra = 0


class FeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 0


class CommentLikesOrDislikesInline(admin.TabularInline):
    model = CommentLikesOrDislikes
    extra = 0


class PositivePointsInline(admin.TabularInline):
    model = PositivePoints
    extra = 0


class NegativePointsInline(admin.TabularInline):
    model = NegativePoints
    extra = 0


class ColorInline(admin.TabularInline):
    model = ProductColor.product.through
    extra = 0


# endregion

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'inventory', 'new_price', 'created', 'updated']
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ['created', 'updated']
    inlines = [ImageInline, FeatureInline, ColorInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['title', 'created', 'user', 'id']
    inlines = [CommentLikesOrDislikesInline, PositivePointsInline, NegativePointsInline]


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['color']
