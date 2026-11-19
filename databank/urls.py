from django.urls import path
from . import views

urlpatterns = [
    # Core & Public Pages
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),

    # User Authentication & Profile
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Dashboard & User Datasets
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('my-datasets/', views.my_datasets, name='my_datasets'),

    # Dataset Management & Exploration
    path('datasets/', views.explore_datasets, name='explore_datasets'),
    path('datasets/upload/', views.upload_dataset, name='dataset_upload'),
    path('datasets/<int:pk>/', views.dataset_detail, name='dataset_detail'),
    path('datasets/<int:pk>/edit/', views.edit_dataset, name='dataset_edit'),
    path('datasets/<int:pk>/delete/', views.delete_dataset, name='dataset_delete'),
    path('datasets/<int:pk>/download/', views.download_dataset_csv, name='dataset_download'),

    # Categories
    path('categories/', views.category_datasets, name='categories'),
    path('categories/<int:category_id>/', views.category_datasets, name='category_detail'),
]
