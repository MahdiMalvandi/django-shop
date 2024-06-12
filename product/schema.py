import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoFilterPaginateListField
from graphene_django_extras.paginations import LimitOffsetGraphqlPagination
from django.db.models.functions import Round
from graphene_file_upload.scalars import Upload

from .models import *
from utils.permissions import admin_required


# region object types
class ProductImagesType(DjangoObjectType):
    class Meta:
        model = Image

    url = graphene.String()

    def resolve_url(self, info):
        if self.file:
            return info.context.build_absolute_uri(self.file.url)
        return None


class ProductFeaturesType(DjangoObjectType):
    class Meta:
        model = ProductFeature
        fields = ('name', 'value')


class PositivePointsType(DjangoObjectType):
    class Meta:
        model = PositivePoints
        fields = "__all__"


class NegativePointsType(DjangoObjectType):
    class Meta:
        model = NegativePoints
        fields = "__all__"


class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = (
            'title', 'content', 'rate', 'positive_points', 'negative_points', 'user', 'product', 'likesOrDislikes')


class ProductColorsType(DjangoObjectType):
    class Meta:
        model = ProductColor
        fields = ('color',)


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = "__all__"


class ProductType(DjangoObjectType):
    average_rating = graphene.Float()

    class Meta:
        model = Product
        interface = (relay.Node,)
        fields = '__all__'
        filter_fields = {
            "id": ("exact",),
            "title": ("icontains", "contains", "istartswith", 'startswith'),
            "slug": ("icontains", "contains",),
            "new_price": ("gt", "lt"),
            "off_percent": ("gt", "lt"),
            "seller__email": ("exact", "istartswith", "icontains", "contains", 'startswith'),
            "seller__id": ("exact",),
            "category__name": ("icontains", "startswith", "istartswith", "contains")
        }

    def resolve_average_rating(self, info):
        return self.average_rating


# endregion object types

# region input objects
class FeatureInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    value = graphene.String(required=True)


class ColorInput(graphene.InputObjectType):
    color = graphene.String(required=True)


# endregion object types

# region mutations
class CategoryMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        parent = graphene.String(required=False)

    category = graphene.Field(CategoryType, required=False)
    success = graphene.Boolean(default_value=False)

    @admin_required
    def mutate(self, info, name, parent=None):
        if Category.objects.filter(name=name).exists():
            raise Exception("A category with this name already exists")
        instance = Category.objects.create(name=name, parent=parent)
        instance.save()
        return CategoryMutation(category=instance, success=True)


class UpdateCategoryMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=False)
        slug = graphene.String(required=True)
        new_slug = graphene.String(required=False)
        parent = graphene.String(required=False)

    category = graphene.Field(CategoryType)
    success = graphene.Boolean(default_value=False)

    @staticmethod
    @admin_required
    def mutate(root, info, slug, name=None, parent_slug=None, new_slug=None):
        if not Category.objects.filter(slug=slug).exists():
            raise Exception("A category with this slug does not already exists")
        instance = Category.objects.get(slug=slug)
        instance.slug = new_slug if new_slug is not None else instance.slug
        instance.name = name if name is not None else instance.name
        if parent_slug is not None:
            parent_category = Category.objects.filter(slug=parent_slug)
            if not parent_category.exists():
                raise Exception("There is no category with this slug to be a parent.")
            instance.parent = parent_category.first() if parent_category.first() is not None else instance.parent
        success = True
        instance.save()
        return UpdateCategoryMutation(category=instance, success=success)


class DeleteCategoryMutation(graphene.Mutation):
    class Arguments:
        slug = graphene.String()

    category = graphene.Field(CategoryType)
    success = graphene.Boolean(default_value=False)

    @staticmethod
    @admin_required
    def mutate(root, info, slug):
        if not Category.objects.filter(slug=slug).exists():
            raise Exception("A category with this name does not already exists")
        instance = Category.objects.get(slug=slug)
        instance.delete()
        success = True
        return DeleteCategoryMutation(category=instance, success=success)


class CreateProductMutation(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        inventory = graphene.Int(required=True)
        price = graphene.Int(required=True)
        off_percent = graphene.Int(required=False)
        seller_username = graphene.String(required=True)
        category_slug = graphene.String(required=True)
        images = graphene.List(Upload, required=False)
        features = graphene.List(FeatureInput, required=False)
        colors = graphene.List(ColorInput, required=False)

    product = graphene.Field(ProductType)
    success = graphene.Boolean(default_value=False)

    @staticmethod
    @admin_required
    def mutate(parent, info, title, inventory, price, seller_username, category_slug, images=None, features=None,
               colors=None, off_percent=None, ):
        if not Category.objects.filter(slug=category_slug).exists():
            raise Exception("A category with this name does not already exists")
        if not User.objects.filter(username=seller_username).exists():
            raise Exception("A User with this username does not already exists")
        category = Category.objects.get(slug=category_slug)
        seller = User.objects.get(username=seller_username)
        product = Product.objects.create(
            title=title,
            inventory=inventory,
            price=price,
            off_percent=off_percent if off_percent is not None else 0,
            seller=seller,
            category=category,
        )

        if images:
            for image in images:
                Image.objects.create(product=product, file=image)

        if colors is not None:
            colors_obj = []
            for color in colors:
                obj, created = ProductColor.objects.get_or_create(color=color['color'])
                colors_obj.append(obj)
            product.colors.set(colors_obj)

        if features is not None:
            ProductFeature.objects.filter(product=product).delete()
            for feature in features:
                ProductFeature.objects.get_or_create(product=product, name=feature['name'], value=feature['value'])
        product.save()
        return CreateProductMutation(product=product, success=True)


class UpdateProductMutation(graphene.Mutation):
    class Arguments:
        slug = graphene.String(required=True)
        title = graphene.String(required=False)
        inventory = graphene.Int(required=False)
        price = graphene.Int(required=False)
        off_percent = graphene.Int(required=False)
        seller_username = graphene.String(required=False)
        category_slug = graphene.String(required=False)
        images = graphene.List(Upload, required=False)
        features = graphene.List(FeatureInput, required=False)
        colors = graphene.List(ColorInput, required=False)
        new_slug = graphene.String(required=False)

    product = graphene.Field(ProductType)
    success = graphene.Boolean(default_value=False)

    @staticmethod
    @admin_required
    def mutate(parent, info, slug, title=None, inventory=None, price=None, seller_username=None, category_slug=None,
               off_percent=None, new_slug=None, colors=None, features=None):
        if category_slug is not None:
            category = Category.objects.filter(slug=slug)
            if not category.exists():
                raise Exception("There is no category with this slug to be a parent.")
            category = category.first()
        else:
            category = None
        if seller_username is not None:
            seller = User.objects.get(username=seller_username)
        else:
            seller = None
        if not Product.objects.filter(slug=slug).exists():
            raise Exception("A product with this name does not already exists")
        product = Product.objects.get(slug=slug)
        product.title = title if title is not None else product.title
        product.inventory = inventory if inventory is not None else product.inventory
        product.price = price if price is not None else product.price
        product.seller = seller if seller is not None else product.seller
        product.category = category if category is not None else product.category
        product.slug = new_slug if new_slug is not None else product.slug
        product.off_percent = off_percent if off_percent is not None else product.off_percent

        if colors is not None:
            colors_obj = []
            for color in colors:
                obj, created = ProductColor.objects.get_or_create(color=color['color'])
                colors_obj.append(obj)
            product.colors.set(colors_obj)

        if features is not None:
            ProductFeature.objects.filter(product=product).delete()
            for feature in features:
                ProductFeature.objects.get_or_create(product=product, name=feature['name'], value=feature['value'])

        # NOTE: Fix for images
        product.save()
        return CreateProductMutation(product=product, success=True)


class DeleteProductMutation(graphene.Mutation):
    class Arguments:
        slug = graphene.String(required=True)

    success = graphene.Boolean(default_value=False)

    @staticmethod
    @admin_required
    def mutate(root, info, slug):
        product = Product.objects.filter(slug=slug)
        if not product.exists():
            raise Exception('There is no product with this slug')
        product.first().delete()
        return DeleteCategoryMutation(success=True)


# endregion

class Query(graphene.ObjectType):
    categories = graphene.List(CategoryType)
    category = graphene.Field(CategoryType, slug=graphene.String())
    products = DjangoFilterPaginateListField(ProductType, pagination=LimitOffsetGraphqlPagination(),
                                             orderBy=graphene.List(of_type=graphene.String))
    product = graphene.Field(ProductType, slug=graphene.String())

    def resolve_categories(parent, info, **kwargs):
        return Category.objects.select_related('parent').all()

    def resolve_products(parent, info, orderBy=None, **kwargs):
        queryset = Product.objects.select_related('seller', 'category').annotate(average_rating=Round(Avg('comments__rate'), 1))
        if orderBy:
            return queryset.order_by(*orderBy)
        return queryset

    def resolve_categoriy(parent, info, **kwargs):
        slug = kwargs.get("slug")
        if slug is not None:
            category = Category.objects.select_related('parent').filter(slug=slug)
            if category.exists():
                return category.first()
            else:
                return Exception('Not Found')
        return Exception('You Have Not sent slug')

    def resolve_product(parent, info, **kwargs):
        slug = kwargs.get("slug")
        if slug is not None:
            product = Product.objects.select_related('seller', 'category').filter(slug=slug)
            if product.exists():
                return product.first()
            else:
                return Exception('Not Found')
        return Exception('You Have Not sent slug')


class Mutation(graphene.ObjectType):
    create_product = CreateProductMutation.Field()
    update_product = UpdateProductMutation.Field()
    delete_product = DeleteProductMutation.Field()
    create_category = CategoryMutation.Field()
    update_category = UpdateCategoryMutation.Field()
    delete_category = DeleteCategoryMutation.Field()
