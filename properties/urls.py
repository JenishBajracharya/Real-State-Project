from rest_framework.routers import DefaultRouter

from .views import (
    AmenityViewSet,
    AreaConverterViewSet,
    DistrictViewSet,
    PropertyImageViewSet,
    PropertyInquiryViewSet,
    PropertyTypeViewSet,
    PropertyViewSet,
)

router = DefaultRouter()
router.register("properties", PropertyViewSet, basename="properties")
router.register("meta/property-types", PropertyTypeViewSet, basename="property-types")
router.register("meta/amenities", AmenityViewSet, basename="amenities")
router.register("meta/districts", DistrictViewSet, basename="districts")
router.register("property-images", PropertyImageViewSet, basename="property-images")
router.register("property-inquiries", PropertyInquiryViewSet, basename="property-inquiries")
router.register("tools/area-converter", AreaConverterViewSet, basename="area-converter")

urlpatterns = router.urls
