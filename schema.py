import graphene
import product.schema
import user.schema
import cart.schema


class Query(product.schema.Query, user.schema.UserQuery, cart.schema.Query):
    pass


class Mutation(product.schema.Mutation, user.schema.Mutation, cart.schema.Mutation):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
