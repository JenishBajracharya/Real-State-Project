from rest_framework import serializers

from .models import Amenity, District, Property, PropertyImage, PropertyInquiry, PropertyType


class PropertyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = ["id", "name"]


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name"]


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ["id", "name", "icon"]


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["id", "property", "image_url", "image_file", "alt_text", "sort_order"]
        extra_kwargs = {"image_url": {"required": False, "allow_blank": True}}


class PropertyInquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyInquiry
        fields = ["id", "property", "name", "email", "phone", "message", "created_at"]
        read_only_fields = ["created_at"]


class PropertyInquiryCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)


class PropertyReadSerializer(serializers.ModelSerializer):
    property_type = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    amenities = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "description",
            "property_type",
            "listing_type",
            "price_amount",
            "price_currency",
            "price_period",
            "address",
            "city",
            "district",
            "latitude",
            "longitude",
            "bedrooms",
            "bathrooms",
            "area_aana",
            "area_sqft",
            "road_width_ft",
            "facing",
            "year_built",
            "is_featured",
            "status",
            "amenities",
            "images",
            "created_at",
            "updated_at",
        ]

    def get_property_type(self, obj):
        return obj.property_type.name if obj.property_type else None

    def get_district(self, obj):
        return obj.district.name if obj.district else None

    def get_amenities(self, obj):
        return [a.name for a in obj.amenities.all()]

    def get_images(self, obj):
        request = self.context.get("request")
        images = []
        for img in obj.images.all():
            if img.image_file:
                if request:
                    images.append(request.build_absolute_uri(img.image_file.url))
                else:
                    images.append(img.image_file.url)
            elif img.image_url:
                images.append(img.image_url)
        return images


class PropertyWriteSerializer(serializers.ModelSerializer):
    property_type = serializers.CharField(required=False, allow_blank=True)
    district = serializers.CharField(required=False, allow_blank=True)
    amenities = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
    image_urls = serializers.ListField(
        child=serializers.URLField(), required=False, allow_empty=True
    )

    class Meta:
        model = Property
        fields = [
            "title",
            "description",
            "property_type",
            "listing_type",
            "price_amount",
            "price_currency",
            "price_period",
            "address",
            "city",
            "district",
            "latitude",
            "longitude",
            "bedrooms",
            "bathrooms",
            "area_aana",
            "area_sqft",
            "road_width_ft",
            "facing",
            "year_built",
            "is_featured",
            "status",
            "amenities",
            "image_urls",
        ]

    def _resolve_property_type(self, name):
        if not name:
            return None
        prop_type, _ = PropertyType.objects.get_or_create(name=name)
        return prop_type

    def _resolve_district(self, name):
        if not name:
            return None
        district, _ = District.objects.get_or_create(name=name)
        return district

    def create(self, validated_data):
        amenities = validated_data.pop("amenities", [])
        image_urls = validated_data.pop("image_urls", [])
        prop_type_name = validated_data.pop("property_type", "")
        district_name = validated_data.pop("district", "")
        validated_data.pop("status", None)

        request = self.context.get("request")
        owner = request.user if request and request.user.is_authenticated else None
        

        prop = Property.objects.create(
            owner=owner,
            property_type=self._resolve_property_type(prop_type_name),
            district=self._resolve_district(district_name),
            status=Property.Status.PENDING,
            **validated_data,
        )

        self._sync_amenities(prop, amenities)
        self._sync_images(prop, image_urls)
        return prop

    def update(self, instance, validated_data):
        amenities = validated_data.pop("amenities", None)
        image_urls = validated_data.pop("image_urls", None)
        prop_type_name = validated_data.pop("property_type", None)
        district_name = validated_data.pop("district", None)

        if prop_type_name is not None:
            instance.property_type = self._resolve_property_type(prop_type_name)
        if district_name is not None:
            instance.district = self._resolve_district(district_name)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if amenities is not None:
            self._sync_amenities(instance, amenities)
        if image_urls is not None:
            self._sync_images(instance, image_urls)

        return instance

    def _sync_amenities(self, prop, amenities):
        prop.amenities.clear()
        for name in amenities:
            if name:
                amenity, _ = Amenity.objects.get_or_create(name=name)
                prop.amenities.add(amenity)

    def _sync_images(self, prop, image_urls):
        prop.images.all().delete()
        for idx, url in enumerate(image_urls):
            if url:
                PropertyImage.objects.create(property=prop, image_url=url, sort_order=idx)
