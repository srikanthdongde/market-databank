from .auth_views import (
    register_view,
    login_view,
    logout_view,
    profile_view,
)
from .dashboard_views import (
    home_view,
    about_view,
    dashboard_view,
)
from .dataset_views import (
    explore_datasets,
    dataset_detail,
    upload_dataset,
    edit_dataset,
    delete_dataset,
    download_dataset_csv,
    my_datasets,
    category_datasets,
)

__all__ = [
    'register_view',
    'login_view',
    'logout_view',
    'profile_view',
    'home_view',
    'about_view',
    'dashboard_view',
    'explore_datasets',
    'dataset_detail',
    'upload_dataset',
    'edit_dataset',
    'delete_dataset',
    'download_dataset_csv',
    'my_datasets',
    'category_datasets',
]
