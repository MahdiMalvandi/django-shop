import graphene
from graphene_django import DjangoObjectType
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
        'title', 'content', 'star', 'positive_points', 'negative_points', 'user', 'product', 'likesOrDislikes')



class ProductColorsType(DjangoObjectType):
    class Meta:
        model = ProductColor
        fields = ('color',)


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = "__all__"


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = '__all__'


# endregion object types

# region input objects
class FeatureInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    value = graphene.String(required=True)


class ColorInput(graphene.InputObjectType):
    color = graphene.String(required=True)


# endregion object types

class CategoryMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        parent = graphene.String()

    category = graphene.Field(CategoryType)
    success = graphene.Boolean(default_value=False)

    @staticmethod
    @admin_required
    def mutate(root, info, name, parent=None):
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
    def mutate(root, info, slug, name=None, parent=None, new_slug=None):
        instance = Category.objects.get(slug=slug)
        instance.slug = new_slug if new_slug is not None else instance.slug
        instance.name = name if name is not None else instance.name
        instance.parent = parent if parent is not None else instance.parent
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

        if features:
            for feature in features:
                ProductFeature.objects.create(product=product, name=feature.name, value=feature.value).save()

        if colors:
            for color in colors:
                ProductColor.objects.create(product=product, color=color.color).save()

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
        category_slug = graphene.String(required=True)
        images = graphene.List(Upload, required=False)
        features = graphene.List(FeatureInput, required=False)
        colors = graphene.List(ColorInput, required=False)
        new_slug = graphene.String(required=False)

    product = graphene.Field(ProductType)
    success = graphene.Boolean(default_value=False)

    @staticmethod
    @admin_required
    def mutate(parent, info, slug, title=None, inventory=None, price=None, seller_username=None, category_slug=None,
               off_percent=None, new_slug=None):
        if category_slug is not None:
            category = Category.objects.get(slug=category_slug)
        else:
            category = None
        if seller_username is not None:
            seller = User.objects.get(username=seller_username)
        else:
            seller = None

        product = Product.objects.get(slug=slug)
        product.title = title if title is not None else product.title
        product.inventory = inventory if inventory is not None else product.inventory
        product.price = price if price is not None else product.price
        product.seller = seller if seller is not None else product.seller
        product.category = category if category is not None else product.category
        product.slug = new_slug if new_slug is not None else product.slug
        product.off_percent = off_percent if off_percent is not None else product.off_percent

        product.save()
        return CreateProductMutation(product=product, success=True)


class DeleteProductMutation(graphene.Mutation):
    class Arguments:
        slug = graphene.String(required=True)

    success = graphene.Boolean(default_value=False)

    @staticmethod
    @admin_required
    def mutate(root, info, slug):
        product = Product.objects.get(slug=slug)
        product.delete()
        return DeleteCategoryMutation(success=True)


class Query(graphene.ObjectType):
    categories = graphene.List(CategoryType)
    category = graphene.Field(CategoryType, slug=graphene.String())
    products = graphene.List(ProductType)
    product = graphene.Field(ProductType, slug=graphene.String())

    def resolve_categories(parent, info, **kwargs):
        return Category.objects.select_related('parent').all()

    def resolve_products(parent, info, **kwargs):
        return Product.objects.select_related('seller', 'category').all()

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
