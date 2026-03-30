from rest_framework.routers import DefaultRouter

from .views import (
    AgentViewSet,
    BlogPostViewSet,
    ContactMessageViewSet,
    FAQViewSet,
    ReviewViewSet,
    ServiceViewSet,
)

router = DefaultRouter()
router.register("agents", AgentViewSet, basename="agents")
router.register("services", ServiceViewSet, basename="services")
router.register("faqs", FAQViewSet, basename="faqs")
router.register("reviews", ReviewViewSet, basename="reviews")
router.register("blog", BlogPostViewSet, basename="blog")
router.register("contact", ContactMessageViewSet, basename="contact")

urlpatterns = router.urls
