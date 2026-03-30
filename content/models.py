from django.db import models
from django.utils.text import slugify

class Agent(models.Model):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone = models.BigIntegerField(blank=True, null=True)
    photo_url= models.URLField(blank=True, null=True)
    bio = models.TextField(blank = True, null = True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name
    

class Service(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    icon = models.CharField(max_length=255, blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title
    
class FAQ( models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField(blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.question

class Review(models.Model):
    name = models.CharField(max_length=255 )
    location = models.CharField(max_length=255, blank=True, null=True)
    rating = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0) 

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__ (self):
        return self.name
    

class BlogPost (models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True )
    category = models.CharField(max_length=255, blank=True, null=True)
    excerpt = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    cover_image_url = models.URLField(blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    read_time_minutes = models.PositiveIntegerField(blank=True, null=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["-published_at", "-id"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    

class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
