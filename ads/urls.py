from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdViewSet,
    ExchangeProposalViewSet,
    UserViewSet,
    AdListView,
    AdDetailView,
    AdCreateView,
    AdUpdateView,
    AdDeleteView,
    ProposalListView,
    CustomLoginView,
    CustomLogoutView,
    RegisterView
)

# Определяем пространство имён приложения
app_name = 'ads'

# DRF API URLs
router = DefaultRouter()
router.register(r'api/ads', AdViewSet, basename='api-ad')
router.register(r'api/proposals', ExchangeProposalViewSet, basename='api-proposal')
router.register(r'api/users', UserViewSet, basename='api-user')

urlpatterns = [
    # API Endpoints
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # HTML Interface - Ads
    path('ads/', AdListView.as_view(), name='ad-list'),
    path('ads/<int:pk>/', AdDetailView.as_view(), name='ad-detail'),
    path('ads/create/', AdCreateView.as_view(), name='ad-create'),
    path('ads/<int:pk>/update/', AdUpdateView.as_view(), name='ad-update'),
    path('ads/<int:pk>/delete/', AdDeleteView.as_view(), name='ad-delete'),

    # HTML Interface - Proposals
    path('proposals/', ProposalListView.as_view(), name='proposal-list'),
    path('proposals/<int:pk>/accept/',
         ExchangeProposalViewSet.as_view({'post': 'accept'}),
         name='proposal-accept'),

    # Auth URLs
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),

    # API Token Auth
    path('api/login/', UserViewSet.as_view({'post': 'login'}), name='api-login'),
    path('api/logout/', UserViewSet.as_view({'post': 'logout'}), name='api-logout'),
]