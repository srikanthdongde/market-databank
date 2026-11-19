import os
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver


class Category(models.Model):
    """
    Model representing market sectors and dataset categories:
    Stock Market, Agriculture, Real Estate, Cryptocurrency, Business and Economics, Other
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon_class = models.CharField(
        max_length=50,
        default='bi-folder2',
        help_text='Bootstrap Icon class (e.g., bi-graph-up, bi-tree, bi-building)'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.name.lower().replace(' ', '-').replace('&', 'and')
        super().save(*args, **kwargs)


class Dataset(models.Model):
    """
    Core Model representing a market dataset.
    Supports CSV uploads, visibility controls (public/private), and parsed metadata.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Detailed description of the dataset contents and context")
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='datasets'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='datasets'
    )
    uploaded_file = models.FileField(
        upload_to='datasets/%Y/%m/',
        help_text="Valid CSV file (maximum 10MB)"
    )
    source = models.CharField(
        max_length=255,
        help_text="Original source or provider (e.g. Yahoo Finance, Kaggle, World Bank, USDA)"
    )
    is_public = models.BooleanField(
        default=True,
        help_text="Public datasets can be viewed and downloaded by community members; private datasets are only accessible to you."
    )
    
    # Metadata extracted automatically upon CSV parsing
    file_size = models.PositiveIntegerField(default=0, help_text="File size in bytes")
    row_count = models.PositiveIntegerField(default=0, help_text="Number of data rows")
    column_count = models.PositiveIntegerField(default=0, help_text="Number of columns")
    column_names = models.TextField(blank=True, help_text="Comma-separated column headers")
    download_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('dataset_detail', kwargs={'pk': self.pk})

    @property
    def filename(self):
        return os.path.basename(self.uploaded_file.name)

    @property
    def file_size_display(self):
        """Format file size in human-readable KB or MB."""
        size = self.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"

    @property
    def columns_list(self):
        """Return column names as a Python list for template rendering."""
        if not self.column_names:
            return []
        return [col.strip() for col in self.column_names.split(',') if col.strip()]


class UserProfile(models.Model):
    """
    Profile extension for Django's built-in User model.
    Stores institutional affiliation and student/researcher bio.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    organization = models.CharField(max_length=150, blank=True, default='Academic / Research')
    bio = models.TextField(blank=True, default='Market data researcher and student contributor.')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Signal to automatically create a profile whenever a new user registers."""
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
