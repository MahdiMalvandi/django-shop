import graphene
import product.schema
import user.schema


class Query(product.schema.Query, user.schema.UserQuery):
    pass


class Mutation(product.schema.Mutation, user.schema.Mutation):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)

