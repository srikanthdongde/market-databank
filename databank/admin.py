from django.contrib import admin
from .models import Category, Dataset, UserProfile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'owner',
        'is_public',
        'row_count',
        'column_count',
        'file_size_display',
        'download_count',
        'created_at'
    )
    list_filter = ('category', 'is_public', 'created_at')
    search_fields = ('title', 'description', 'source', 'owner__username')
    readonly_fields = ('file_size', 'row_count', 'column_count', 'column_names', 'download_count', 'created_at', 'updated_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'created_at')
    search_fields = ('user__username', 'user__email', 'organization')
