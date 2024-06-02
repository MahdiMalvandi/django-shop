from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from graphene_django.views import GraphQLView

from django_shop import settings

urlpatterns = [
    path('admin/', admin.site.urls),

    path(r"api/", GraphQLView.as_view(graphiql=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
