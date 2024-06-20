import graphene
import product.schema
import user.schema
import cart.schema
import ticket.schema
import discount_code.schema
import order.schema


class Query(product.schema.Query, user.schema.UserQuery, cart.schema.Query, ticket.schema.Query,
            discount_code.schema.Query, order.schema.Query):
    pass


class Mutation(product.schema.Mutation, user.schema.Mutation, cart.schema.Mutation, ticket.schema.Mutation,
               discount_code.schema.Mutation, order.schema.Mutation):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
