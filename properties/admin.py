from django.contrib import admin
from .models import Property, Amenity, District, PropertyImage, PropertyInquiry, PropertyType

# Register your models here.

@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    search_fields = ("name",)

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    search_fields = ("name",)

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

@admin.register(Property)
class PropertyAdmin (admin.ModelAdmin):
    list_display = ("title", "listing_type", "price_amount", "status", "is_featured")
    list_filter = ("listing_type", "status", "is_featured", "district")
    search_fields = ("title", "address")
    inlines = [PropertyImageInline]

@admin.register(PropertyInquiry)
class PropertInquiryAdmin(admin.ModelAdmin):
    list_display = ("property", "name", "email", "created_at")
    search_fields = ("name","email", "property_title")

    