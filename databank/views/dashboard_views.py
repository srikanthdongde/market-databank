import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from ..models import Dataset, Category


def home_view(request):
    """
    Public landing page for the Market Databank Generation and Sharing Platform.
    Provides platform overview, metrics, and highlights recent datasets.
    """
    total_public_datasets = Dataset.objects.filter(is_public=True).count()
    categories = Category.objects.annotate(
        pub_count=Count('datasets', filter=Q(datasets__is_public=True))
    )
    total_users = User.objects.count()
    recent_public_datasets = Dataset.objects.filter(is_public=True).select_related('category', 'owner')[:6]

    context = {
        'total_public_datasets': total_public_datasets,
        'categories': categories,
        'total_users': total_users,
        'recent_datasets': recent_public_datasets,
    }
    return render(request, 'core/home.html', context)


def about_view(request):
    """
    Information page explaining the project architecture, tech stack,
    data governance, and academic purpose.
    """
    return render(request, 'core/about.html')


@login_required
def dashboard_view(request):
    """
    Personalized analytics dashboard displaying real database counts,
    user-specific uploads, category distributions for Chart.js, and recent activity.
    """
    user = request.user
    
    # Meaningful statistics computed from actual database records
    my_datasets_qs = Dataset.objects.filter(owner=user)
    my_datasets_count = my_datasets_qs.count()
    my_public_count = my_datasets_qs.filter(is_public=True).count()
    my_private_count = my_datasets_qs.filter(is_public=False).count()

    # Total public datasets on the platform
    total_public_count = Dataset.objects.filter(is_public=True).count()
    
    # Total datasets accessible to this user (all public + own private)
    accessible_datasets = Dataset.objects.filter(Q(is_public=True) | Q(owner=user)).distinct()
    total_accessible_count = accessible_datasets.count()

    # Category breakdown for Chart.js (based on real database records)
    categories = Category.objects.annotate(
        user_cat_count=Count('datasets', filter=Q(datasets__owner=user)),
        total_cat_count=Count('datasets', filter=Q(datasets__is_public=True) | Q(datasets__owner=user))
    ).order_by('name')

    cat_labels = [cat.name for cat in categories]
    cat_counts = [cat.total_cat_count for cat in categories]
    cat_my_counts = [cat.user_cat_count for cat in categories]

    # Recently uploaded by current user
    my_recent = my_datasets_qs.select_related('category').order_by('-created_at')[:5]

    # Recently uploaded across community (public or owned by user)
    community_recent = accessible_datasets.select_related('category', 'owner').order_by('-created_at')[:6]

    context = {
        'total_accessible_count': total_accessible_count,
        'my_datasets_count': my_datasets_count,
        'my_public_count': my_public_count,
        'my_private_count': my_private_count,
        'total_public_count': total_public_count,
        'categories': categories,
        'my_recent': my_recent,
        'community_recent': community_recent,
        # JSON serialized for clean Chart.js consumption in template
        'chart_labels_json': json.dumps(cat_labels),
        'chart_counts_json': json.dumps(cat_counts),
        'chart_my_counts_json': json.dumps(cat_my_counts),
        'visibility_data_json': json.dumps([my_public_count, my_private_count]),
    }
    return render(request, 'datasets/dashboard.html', context)
