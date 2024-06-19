import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoFilterPaginateListField
from graphene_django_extras.paginations import LimitOffsetGraphqlPagination
from django.db.models.functions import Round
from graphene_file_upload.scalars import Upload
from graphql_jwt.decorators import login_required

from .models import *
from utils.permissions import admin_required


# region object types
class ProductImagesType(DjangoObjectType):
    class Meta:
        model = Image

    url = graphene.String()

    def resolve_url(self, info):
        """ returning the product images url """
        if self.file:
            return info.context.build_absolute_uri(self.file.url)
        return None


class ProductFeaturesType(DjangoObjectType):
    class Meta:
        model = ProductFeature
        fields = ('name', 'value')


class CommentLikesOrDislikesType(DjangoObjectType):
    class Meta:
        model = CommentLikesOrDislikes
        fields = ["user", "comment", "content"]


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
            'title', 'content', 'rate', 'positive_points', 'negative_points', 'user', 'product', 'likes_or_dislikes')


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
        # validate category and create
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
        # validate
        try:
            category = Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            raise Exception("A category with this slug does not already exists")
        instance = category
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
        category_slug = graphene.String(required=True)
        images = graphene.List(Upload, required=False)
        features = graphene.List(FeatureInput, required=False)
        colors = graphene.List(ColorInput, required=False)

    product = graphene.Field(ProductType)
    success = graphene.Boolean(default_value=False)

    @staticmethod
    @admin_required
    def mutate(parent, info, title, inventory, price, category_slug, images=None, features=None,
               colors=None, off_percent=None, ):
        # validate category and get it
        try:
            category = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            raise Exception("A category with this slug does not already exists")

        # get user
        seller = info.context.user

        # create product object
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
        category_slug = graphene.String(required=False)
        images = graphene.List(Upload, required=False)
        features = graphene.List(FeatureInput, required=False)
        colors = graphene.List(ColorInput, required=False)
        new_slug = graphene.String(required=False)

    product = graphene.Field(ProductType)
    success = graphene.Boolean(default_value=False)

    @staticmethod
    @admin_required
    def mutate(parent, info, slug, title=None, inventory=None, price=None, category_slug=None,
               off_percent=None, new_slug=None, colors=None, features=None):
        if category_slug is not None:
            # validate category and get it
            try:
                category = Category.objects.get(slug=category_slug)
            except Category.DoesNotExist:
                raise Exception("A category with this slug does not already exists")
        else:
            category = None

        # validate product and get it
        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            raise Exception("A product with this slug does not already exists")
        product.title = title if title is not None else product.title
        product.inventory = inventory if inventory is not None else product.inventory
        product.price = price if price is not None else product.price
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
        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            raise Exception('There is no product with this slug')
        product.delete()
        return DeleteCategoryMutation(success=True)


class CreateCommentMutation(graphene.Mutation):
    class Arguments:
        content = graphene.String(required=True)
        title = graphene.String(required=True)
        positive_points = graphene.List(graphene.String, required=False)
        negative_points = graphene.List(graphene.String, required=False)
        product_slug = graphene.String(required=True)
        rate = graphene.Int(required=True)

    comment = graphene.Field(CommentType)
    success = graphene.Boolean(default_value=False)

    @login_required
    def mutate(self, info, content, title, product_slug, rate, positive_points=None, negative_points=None):
        user = info.context.user

        # get product
        try:
            product = Product.objects.get(slug=product_slug)
        except Product.DoesNotExist:
            raise Exception('a product with this slug does not exist')

        # validation rate
        rate_choice = [1, 2, 3, 4, 5]
        if rate not in rate_choice:
            raise Exception('rate must be an integer between 1 and 5')

        # create comment object
        obj = Comment.objects.create(content=content, product=product, rate=rate, user=user, title=title)

        # create positive points
        if positive_points is not None:
            for point in positive_points:
                PositivePoints.objects.create(comment=obj, content=point)

        # create negative points
        if negative_points is not None:
            for point in negative_points:
                NegativePoints.objects.create(comment=obj, content=point)
        return CreateCommentMutation(success=True, comment=obj)


class UpdateCommentMutation(graphene.Mutation):
    class Arguments:
        content = graphene.String(required=False)
        title = graphene.String(required=False)
        id = graphene.Int(required=True)
        positive_points = graphene.List(graphene.String, required=False)
        negative_points = graphene.List(graphene.String, required=False)
        product_slug = graphene.String(required=False)
        rate = graphene.Int(required=False)

    comment = graphene.Field(CommentType)
    success = graphene.Boolean(default_value=False)

    @admin_required
    def mutate(self, info, id, content=None, title=None, product_slug=None, rate=None, positive_points=None,
               negative_points=None):
        # validation rate
        if rate is not None:
            rate_choice = [1, 2, 3, 4, 5]
            if rate not in rate_choice:
                raise Exception('rate must be an integer between 1 and 5')

        # get product
        if product_slug is not None:
            try:
                product = Product.objects.get(slug=product_slug)
            except Product.DoesNotExist:
                raise Exception('a product with this slug does not exist')
        else:
            product = None

        # create comment object
        try:
            comment = Comment.objects.get(id=id)
        except Comment.DoesNotExist:
            raise Exception('a comment with this id does not exist')

        # create positive points
        if positive_points is not None:
            comment.positive_points.all().delete()
            for point in positive_points:
                PositivePoints.objects.get_or_create(comment=comment, content=point)

        # create negative points
        if negative_points is not None:
            comment.negative_points.all().delete()
            for point in negative_points:
                NegativePoints.objects.get_or_create(comment=comment, content=point)

        # update comment fields
        comment.title = title if title is not None else comment.title
        comment.content = content if content is not None else comment.content
        comment.product = product if product is not None else comment.product
        comment.save()
        return UpdateCommentMutation(success=True, comment=comment)


class DeleteCommentMutation(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean(default_value=False)

    @staticmethod
    @admin_required
    def mutate(root, info, id):
        try:
            comment = Comment.objects.get(id=id)
        except Comment.DoesNotExist:
            raise Exception('There is no comment with this id')
        comment.delete()
        return DeleteCommentMutation(success=True)


class LikeOrDislikeCommentMutation(graphene.Mutation):
    class Arguments:
        content = graphene.String(required=True)
        comment_id = graphene.Int(required=True)

    success = graphene.Boolean(default_value=False)
    object = graphene.Field(CommentLikesOrDislikesType)

    @login_required
    def mutate(root, info, comment_id, content):
        # validate content
        like_dislike_word = ['liked', 'disliked']
        if content.lower() not in like_dislike_word:
            raise Exception('content must be "liked" or "disliked"')

        # get the comment
        try:
            comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            raise Exception('There is no comment with this id')

        # get user
        user = info.context.user

        # create like or dislike object
        obj = CommentLikesOrDislikes.objects.create(user=user, content=content.lower(), comment=comment)
        return LikeOrDislikeCommentMutation(success=True, object=obj)


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
        queryset = Product.objects.select_related('seller', 'category').annotate(
            average_rating=Round(Avg('comments__rate'), 1))
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
    create_comment = CreateCommentMutation.Field()
    update_comment = UpdateCommentMutation.Field()
    delete_comment = DeleteCommentMutation.Field()
    like_or_dislike_comment = LikeOrDislikeCommentMutation.Field()
