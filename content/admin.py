from django.contrib import admin

from .models import Agent, BlogPost, ContactMessage, FAQ, Review, Service


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "is_active")
    search_fields = ("name", "role", "email")
    list_filter = ("is_active",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    search_fields = ("title",)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    search_fields = ("question",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    search_fields = ("name", "location")


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_published", "published_at")
    search_fields = ("title", "category")
    list_filter = ("is_published", "category")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email", "subject")
