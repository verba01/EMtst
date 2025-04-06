from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib.auth.views import LogoutView

schema_view = get_schema_view(
    openapi.Info(
        title="Barter System API",
        default_version='v1',
        description="API for item exchange platform",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@barter.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('ads.urls')),
path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

   
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
    path('swagger/',
         schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    path('redoc/',
         schema_view.with_ui('redoc', cache_timeout=0),
         name='schema-redoc'),

   
    path('accounts/logout/', LogoutView.as_view(next_page='/swagger/'), name='logout'),
]
