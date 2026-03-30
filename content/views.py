from rest_framework import permissions, viewsets
from .models import Agent, Service, FAQ, Review, BlogPost, ContactMessage
from .serializers import AgentSerializer, ServiceSerializer, FAQSerializer, ReviewSerializer, BlogPostSerializer, ContactMessageSerializer


class AgentViewSet(viewsets.ModelViewSet):
    serializer_class = AgentSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Agent.objects.all().order_by("sort_order", "id")
        if not self.request.user.is_authenticated:
            qs = qs.filter(is_active=True)
        return qs
    
class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all().order_by("sort_order", "id")
    serializer_class = ServiceSerializer
    permission_classes = [permissions.AllowAny]

class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all().order_by("sort_order", "id")
    serializer_class = FAQSerializer
    permission_classes = [permissions.AllowAny]


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all().order_by("sort_order", "id")
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

class BlogPostViewSet(viewsets.ModelViewSet):
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        qs = BlogPost.objects.all().order_by("-published_at", "-id")
        if self.action in ["list", "retrieve"] and not self.request.user.is_authenticated:
            qs = qs.filter(is_published=True)
        return qs
    

class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all().order_by("-created_at", "-id")
    serializer_class = ContactMessageSerializer

    def get_permissions(self):
        if self.action =="create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
