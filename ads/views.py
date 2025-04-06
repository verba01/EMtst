from django.contrib.auth import logout, authenticate
from django.contrib import messages
from django.shortcuts import redirect
from rest_framework import viewsets, status, filters, serializers
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from rest_framework import viewsets, status, filters
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from .models import Ad, ExchangeProposal
from .serializers import AdSerializer, ExchangeProposalSerializer, UserSerializer
from django_filters.rest_framework import DjangoFilterBackend


# HTML Views
class AdListView(ListView):
    model = Ad
    template_name = 'ads/ad_list.html'
    context_object_name = 'ads'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at')
        if self.request.GET.get('category'):
            queryset = queryset.filter(category=self.request.GET['category'])
        if self.request.GET.get('condition'):
            queryset = queryset.filter(condition=self.request.GET['condition'])
        if self.request.GET.get('search'):
            queryset = queryset.filter(
                Q(title__icontains=self.request.GET['search']) |
                Q(description__icontains=self.request.GET['search'])
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_choices'] = Ad.CATEGORY_CHOICES
        context['condition_choices'] = Ad.CONDITION_CHOICES
        return context


class AdDetailView(DetailView):
    model = Ad
    template_name = 'ads/ad_detail.html'
    context_object_name = 'ad'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and self.request.user != self.object.user:
            context['user_ads'] = Ad.objects.filter(user=self.request.user)
        return context


class AdCreateView(LoginRequiredMixin, CreateView):
    model = Ad
    template_name = 'ads/ad_form.html'
    fields = ['title', 'description', 'image_url', 'category', 'condition']

    def form_valid(self, form):
        if not self.request.FILES.get('image'):
            messages.error(self.request, "Пожалуйста, прикрепите фото")
            return self.form_invalid(form)

        # Сохраняем объявление с автором
        ad = form.save(commit=False)
        ad.author = self.request.user
        ad.save()

        return redirect('ads:ad-list')


class AdUpdateView(LoginRequiredMixin, UpdateView):
    model = Ad
    template_name = 'ads/ad_form.html'
    fields = ['title', 'description', 'image_url', 'category', 'condition']

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != request.user:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AdDeleteView(LoginRequiredMixin, DeleteView):
    model = Ad
    template_name = 'ads/ad_confirm_delete.html'
    success_url = reverse_lazy('ads:ad-list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != request.user:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class ProposalListView(LoginRequiredMixin, ListView):
    model = ExchangeProposal
    template_name = 'ads/proposal_list.html'
    context_object_name = 'proposals'
    paginate_by = 10

    def get_queryset(self):
        active_tab = self.request.GET.get('type', 'received')
        if active_tab == 'received':
            return ExchangeProposal.objects.filter(
                ad_receiver__user=self.request.user
            ).order_by('-created_at')
        return ExchangeProposal.objects.filter(
            ad_sender__user=self.request.user
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = self.request.GET.get('type', 'received')
        return context


# DRF API Views
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = []

    @action(detail=False, methods=['post'])
    def login(self, request):
        user = authenticate(
            username=request.data.get('username'),
            password=request.data.get('password')
        )
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        if request.user.is_authenticated:
            Token.objects.filter(user=request.user).delete()
            logout(request)
            return Response({"detail": "Successfully logged out."})
        return Response({"detail": "You're not logged in."}, status=status.HTTP_400_BAD_REQUEST)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all().order_by('-created_at')
    serializer_class = AdSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'condition']
    search_fields = ['title', 'description']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.user != self.request.user:
            return Response(
                {'error': 'Вы не можете редактировать это объявление'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()


class ExchangeProposalViewSet(viewsets.ModelViewSet):
    queryset = ExchangeProposal.objects.all().order_by('-created_at')
    serializer_class = ExchangeProposalSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ad_sender', 'ad_receiver', 'status']

    def perform_create(self, serializer):
        ad_sender = serializer.validated_data['ad_sender']
        ad_receiver = serializer.validated_data['ad_receiver']

        if ad_sender.user != self.request.user:
            raise serializers.ValidationError(
                "Вы можете создавать предложения только от своих объявлений"
            )
        if ad_sender.user == ad_receiver.user:
            raise serializers.ValidationError(
                "Нельзя создавать предложения на свои же объявления"
            )
        serializer.save()

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        proposal = self.get_object()
        if proposal.ad_receiver.user != request.user:
            return Response(
                {'error': 'Вы не можете принять это предложение'},
                status=status.HTTP_403_FORBIDDEN
            )
        proposal.status = 'accepted'
        proposal.save()
        return Response({'status': 'Предложение принято'})


# Auth Views
class CustomLoginView(LoginView):
    template_name = 'ads/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('ads:ad-list')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('ads:ad-list')


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'ads/register.html'
    success_url = reverse_lazy('ads:login')