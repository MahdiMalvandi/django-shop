from django.db import models
from user.models import User
import json


def image_profile_upload_path(instance, filename):
    return f"products/images/{instance.product.title}/{filename}"


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.CharField(max_length=255, blank=True, null=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

    def save(
            self, *args, **kwargs
    ):
        if self.slug is None:
            self.slug = self.name.replace(' ', '-')
        else:
            self.slug = self.slug
        super(Category, self).save(*args, **kwargs)


class Product(models.Model):
    title = models.CharField(max_length=255, unique=True)
    slug = models.CharField(max_length=255, blank=True, null=True)
    inventory = models.IntegerField()
    price = models.IntegerField()
    off_percent = models.IntegerField(blank=True, null=True, default=0)
    new_price = models.IntegerField(blank=True, null=True, default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    seller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')

    def save(
            self, *args, **kwargs
    ):
        if self.slug is None:

            self.slug = self.title.replace(' ', '-')
        else:
            self.slug = self.slug

        if self.off_percent > 0:
            self.new_price = self.price - ((self.price * self.off_percent) / 100)
        else:
            self.new_price = self.price
        super(Product, self).save(*args, **kwargs)


class Image(models.Model):
    file = models.ImageField(upload_to=image_profile_upload_path)
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)


class ProductFeature(models.Model):
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    product = models.ForeignKey(Product, related_name='features', on_delete=models.CASCADE)


class ProductColor(models.Model):
    color = models.CharField(max_length=255)
    product = models.ManyToManyField(Product, related_name='colors')


class Comment(models.Model):
    star_field = (
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
    )
    title = models.CharField(max_length=255)
    content = models.TextField(max_length=500)
    star = models.IntegerField(choices=star_field)
    product = models.ForeignKey(Product, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)


class CommentLikesOrDislikes(models.Model):
    like_choice = (
        ('0', 'liked'),
        ('1', 'disliked')
    )
    user = models.ForeignKey(User, related_name='likesOrDislikes', on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, related_name='likesOrDislikes', on_delete=models.CASCADE)
    content = models.CharField(choices=like_choice)


class PositivePoints(models.Model):
    comment = models.ForeignKey(Comment, related_name='positive_points', on_delete=models.CASCADE)
    content = models.CharField()


class NegativePoints(models.Model):
    comment = models.ForeignKey(Comment, related_name='negative_points', on_delete=models.CASCADE)
    content = models.CharField()
