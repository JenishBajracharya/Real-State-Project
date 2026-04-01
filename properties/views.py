from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Amenity, District, Property, PropertyImage, PropertyInquiry, PropertyType
from .serializers import (
    AmenitySerializer,
    DistrictSerializer,
    PropertyImageSerializer,
    PropertyInquiryCreateSerializer,
    PropertyInquirySerializer,
    PropertyReadSerializer,
    PropertyTypeSerializer,
    PropertyWriteSerializer,
)


class PropertyViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Property.objects.select_related("property_type", "district").prefetch_related(
            "amenities", "images")
    
        if self.action == "list" and not self.request.user.is_authenticated:
            qs = qs.filter(status=Property.Status.PUBLISHED)

        search = self.request.query_params.get("search", "").strip()
        listing_type = self.request.query_params.get("listing_type")
        property_type = self.request.query_params.get("property_type")
        district = self.request.query_params.get("district")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        bedrooms = self.request.query_params.get("bedrooms")
        bathrooms = self.request.query_params.get("bathrooms")

        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(address__icontains=search))
        if listing_type:
            qs = qs.filter(listing_type=listing_type)
        if property_type:
            qs = qs.filter(property_type__name__iexact=property_type)
        if district:
            qs = qs.filter(district__name__iexact=district)
        if min_price:
            qs = qs.filter(price_amount__gte=min_price)
        if max_price:
            qs = qs.filter(price_amount__lte=max_price)
        if bedrooms:
            qs = qs.filter(bedrooms__gte=bedrooms)
        if bathrooms:
            qs = qs.filter(bathrooms__gte=bathrooms)

        return qs

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PropertyWriteSerializer
        return PropertyReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        read_serializer = PropertyReadSerializer(instance, context=self.get_serializer_context())
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        read_serializer = PropertyReadSerializer(instance, context=self.get_serializer_context())
        return Response(read_serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).order_by("-created_at")[:50]
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        url_path="inquiries",
        permission_classes=[permissions.AllowAny],
    )
    def inquiries(self, request, pk=None):
        prop = self.get_object()
        serializer = PropertyInquiryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        PropertyInquiry.objects.create(property=prop, **serializer.validated_data)
        return Response({"detail": "Inquiry sent."}, status=status.HTTP_201_CREATED)


class PropertyTypeViewSet(viewsets.ModelViewSet):
    queryset = PropertyType.objects.all().order_by("name")
    serializer_class = PropertyTypeSerializer
    permission_classes = [permissions.AllowAny]


class AmenityViewSet(viewsets.ModelViewSet):
    queryset = Amenity.objects.all().order_by("name")
    serializer_class = AmenitySerializer
    permission_classes = [permissions.AllowAny]


class DistrictViewSet(viewsets.ModelViewSet):
    queryset = District.objects.all().order_by("name")
    serializer_class = DistrictSerializer
    permission_classes = [permissions.AllowAny]


class PropertyImageViewSet(viewsets.ModelViewSet):
    queryset = PropertyImage.objects.all().order_by("sort_order", "id")
    serializer_class = PropertyImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class PropertyInquiryViewSet(viewsets.ModelViewSet):
    queryset = PropertyInquiry.objects.all().order_by("-created_at", "-id")
    serializer_class = PropertyInquirySerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


class AreaConverterViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        def _to_float(val):
            try:
                return float(val)
            except (TypeError, ValueError):
                return None

        units = {
            "aana": 342.25,
            "sqft": 1.0,
            "ropani": 16 * 342.25,
            "paisa": 342.25 / 4,
            "dam": 342.25 / 16,
            "bigha": 20 * 182.25,
            "kattha": 182.25,
            "dhur": 182.25 / 20,
        }

        from_unit = request.query_params.get("from_unit")
        to_unit = request.query_params.get("to_unit")
        value = _to_float(request.query_params.get("value"))

        conversion = None
        if from_unit and to_unit and value is not None:
            from_unit_key = from_unit.lower()
            to_unit_key = to_unit.lower()
            if from_unit_key in units and to_unit_key in units:
                sqft_value = value * units[from_unit_key]
                conversion = {
                    "from_unit": from_unit_key,
                    "to_unit": to_unit_key,
                    "input": value,
                    "output": round(sqft_value / units[to_unit_key], 6),
                }

        data = {
            "updated_at": timezone.now().isoformat(),
            "conversion": conversion,
            "units": {
                "ropani": {"aana": 16, "paisa": 64, "dam": 256},
                "bigha": {"kattha": 20, "dhur": 400},
                "sqft_per_aana": 342.25,
                "sqft_per_dhur": 182.25,
            },
        }
        return Response(data)
