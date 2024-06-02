from django.db import models
from user.models import User


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
            self,*args, **kwargs
    ):
        if self.slug is None:

            self.slug = self.title.replace(' ', '-')
        else:
            self.slug = self.slug

        self.new_price = self.price - ((self.price * self.off_percent) / 100)
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
    product = models.ForeignKey(Product, related_name='colors', on_delete=models.CASCADE)
