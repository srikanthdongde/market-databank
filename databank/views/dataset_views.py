import os
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, Http404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone

from ..models import Dataset, Category
from ..forms import DatasetForm, DatasetEditForm
from ..utils import get_csv_preview


def explore_datasets(request):
    """
    Explore, search, filter, and sort datasets.
    Strictly enforces public/private access rules at the ORM queryset level.
    """
    # 1. Base Queryset with strict privacy control
    if request.user.is_authenticated:
        base_qs = Dataset.objects.filter(Q(is_public=True) | Q(owner=request.user))
    else:
        base_qs = Dataset.objects.filter(is_public=True)

    base_qs = base_qs.select_related('category', 'owner')

    # 2. Text Search (title, description, source, column names)
    query = request.GET.get('q', '').strip()
    if query:
        base_qs = base_qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(source__icontains=query) |
            Q(column_names__icontains=query)
        )

    # 3. Category Filter
    category_id = request.GET.get('category')
    selected_category = None
    if category_id:
        try:
            base_qs = base_qs.filter(category_id=int(category_id))
            selected_category = Category.objects.filter(pk=int(category_id)).first()
        except ValueError:
            pass

    # 4. Date Filter
    date_filter = request.GET.get('date', 'all')
    now = timezone.now()
    if date_filter == 'today':
        base_qs = base_qs.filter(created_at__date=now.date())
    elif date_filter == 'week':
        base_qs = base_qs.filter(created_at__gte=now - timedelta(days=7))
    elif date_filter == 'month':
        base_qs = base_qs.filter(created_at__gte=now - timedelta(days=30))
    elif date_filter == 'year':
        base_qs = base_qs.filter(created_at__gte=now - timedelta(days=365))

    # 5. Visibility Filter (for logged-in users who own private datasets)
    visibility_filter = request.GET.get('visibility', 'all')
    if request.user.is_authenticated:
        if visibility_filter == 'public':
            base_qs = base_qs.filter(is_public=True)
        elif visibility_filter == 'private':
            base_qs = base_qs.filter(is_public=False, owner=request.user)

    # 6. Sorting
    sort_option = request.GET.get('sort', 'newest')
    if sort_option == 'oldest':
        base_qs = base_qs.order_by('created_at')
    elif sort_option == 'rows_desc':
        base_qs = base_qs.order_by('-row_count')
    elif sort_option == 'size_desc':
        base_qs = base_qs.order_by('-file_size')
    elif sort_option == 'downloads':
        base_qs = base_qs.order_by('-download_count')
    else:  # newest default
        base_qs = base_qs.order_by('-created_at')

    # 7. Pagination (9 cards per page)
    paginator = Paginator(base_qs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # All categories with count of accessible datasets
    categories = Category.objects.annotate(
        count=Count(
            'datasets',
            filter=Q(datasets__is_public=True) | (Q(datasets__owner=request.user) if request.user.is_authenticated else Q(pk__isnull=True))
        )
    )

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': selected_category,
        'selected_category_id': category_id,
        'date_filter': date_filter,
        'visibility_filter': visibility_filter,
        'sort_option': sort_option,
        'total_results': base_qs.count(),
    }
    return render(request, 'datasets/explore.html', context)


def dataset_detail(request, pk):
    """
    Display comprehensive dataset details, column schema, metadata,
    and a tabular preview of the first 15-20 rows of the CSV file.
    Enforces privacy access rules.
    """
    dataset = get_object_or_404(Dataset.objects.select_related('category', 'owner'), pk=pk)

    # Security check: Private dataset can only be viewed by its owner
    if not dataset.is_public:
        if not request.user.is_authenticated or dataset.owner != request.user:
            raise PermissionDenied("This dataset is private. Only the creator has permission to view it.")

    # Generate CSV preview data
    preview_data = get_csv_preview(dataset.uploaded_file, max_rows=20)

    # Check ownership
    is_owner = request.user.is_authenticated and (dataset.owner == request.user)

    context = {
        'dataset': dataset,
        'preview_headers': preview_data.get('headers', []),
        'preview_rows': preview_data.get('rows', []),
        'total_preview_rows': preview_data.get('total_preview_rows', 0),
        'chart_column_name': preview_data.get('chart_column_name', ''),
        'chart_labels': preview_data.get('chart_labels', []),
        'chart_values': preview_data.get('chart_values', []),
        'is_owner': is_owner,
    }
    return render(request, 'datasets/detail.html', context)


@login_required
def upload_dataset(request):
    """
    Form view to upload a new market dataset with CSV validation and metadata extraction.
    """
    if request.method == 'POST':
        form = DatasetForm(request.POST, request.FILES)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.owner = request.user

            # Apply parsed metadata from validation step
            metadata = getattr(form, 'parsed_metadata', {})
            if metadata:
                dataset.file_size = metadata.get('file_size', 0)
                dataset.row_count = metadata.get('row_count', 0)
                dataset.column_count = metadata.get('column_count', 0)
                dataset.column_names = metadata.get('column_names', '')

            dataset.save()
            messages.success(
                request,
                f"Dataset '{dataset.title}' successfully uploaded and indexed! ({dataset.row_count:,} rows, {dataset.column_count} columns parsed)."
            )
            return redirect('dataset_detail', pk=dataset.pk)
        else:
            messages.error(request, "Failed to upload dataset. Please check the file format and required fields below.")
    else:
        form = DatasetForm()

    return render(request, 'datasets/upload.html', {'form': form})


@login_required
def edit_dataset(request, pk):
    """
    Edit dataset metadata. Only the dataset owner can edit.
    """
    dataset = get_object_or_404(Dataset, pk=pk)

    if dataset.owner != request.user:
        raise PermissionDenied("You can only edit datasets that you own.")

    if request.method == 'POST':
        form = DatasetEditForm(request.POST, request.FILES, instance=dataset)
        if form.is_valid():
            updated_dataset = form.save(commit=False)

            # If a new CSV was uploaded, update the parsed metadata
            metadata = getattr(form, 'parsed_metadata', None)
            if metadata:
                updated_dataset.file_size = metadata.get('file_size', 0)
                updated_dataset.row_count = metadata.get('row_count', 0)
                updated_dataset.column_count = metadata.get('column_count', 0)
                updated_dataset.column_names = metadata.get('column_names', '')

            updated_dataset.save()
            messages.success(request, f"Dataset '{updated_dataset.title}' updated successfully.")
            return redirect('dataset_detail', pk=updated_dataset.pk)
        else:
            messages.error(request, "Please fix the errors in the update form.")
    else:
        form = DatasetEditForm(instance=dataset)

    return render(request, 'datasets/edit.html', {'form': form, 'dataset': dataset})


@login_required
def delete_dataset(request, pk):
    """
    Delete a dataset and its associated CSV file from disk.
    Strictly restricted to the owner.
    """
    dataset = get_object_or_404(Dataset, pk=pk)

    if dataset.owner != request.user:
        raise PermissionDenied("You can only delete datasets that you have created.")

    if request.method == 'POST':
        title = dataset.title
        # Safely remove file from filesystem if present
        if dataset.uploaded_file and os.path.isfile(dataset.uploaded_file.path):
            try:
                os.remove(dataset.uploaded_file.path)
            except OSError:
                pass

        dataset.delete()
        messages.success(request, f"Dataset '{title}' has been permanently deleted.")
        return redirect('my_datasets')

    # If accessed via GET, render a confirmation page or redirect
    return render(request, 'datasets/delete_confirm.html', {'dataset': dataset})


def download_dataset_csv(request, pk):
    """
    Secure file download view:
    - Verifies private/public access rules.
    - Increments download counter.
    - Streams file safely as an attachment.
    """
    dataset = get_object_or_404(Dataset, pk=pk)

    # Privacy enforcement
    if not dataset.is_public:
        if not request.user.is_authenticated or dataset.owner != request.user:
            raise PermissionDenied("You do not have permission to download this private dataset.")

    if not dataset.uploaded_file or not os.path.exists(dataset.uploaded_file.path):
        raise Http404("The requested file was not found on the server.")

    # Increment download counter
    Dataset.objects.filter(pk=pk).update(download_count=dataset.download_count + 1)

    file_handle = open(dataset.uploaded_file.path, 'rb')
    response = FileResponse(file_handle, as_attachment=True, filename=dataset.filename)
    response['Content-Type'] = 'text/csv'
    return response


@login_required
def my_datasets(request):
    """
    View displaying all datasets uploaded by the current authenticated user.
    """
    user_datasets = Dataset.objects.filter(owner=request.user).select_related('category').order_by('-created_at')

    query = request.GET.get('q', '').strip()
    if query:
        user_datasets = user_datasets.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    visibility = request.GET.get('visibility', 'all')
    if visibility == 'public':
        user_datasets = user_datasets.filter(is_public=True)
    elif visibility == 'private':
        user_datasets = user_datasets.filter(is_public=False)

    paginator = Paginator(user_datasets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'visibility': visibility,
        'total_user_datasets': Dataset.objects.filter(owner=request.user).count(),
        'total_public': Dataset.objects.filter(owner=request.user, is_public=True).count(),
        'total_private': Dataset.objects.filter(owner=request.user, is_public=False).count(),
    }
    return render(request, 'datasets/my_datasets.html', context)


def category_datasets(request, category_id=None):
    """
    Browse datasets organized by market sectors/categories.
    """
    categories = Category.objects.annotate(
        dataset_count=Count(
            'datasets',
            filter=Q(datasets__is_public=True) | (Q(datasets__owner=request.user) if request.user.is_authenticated else Q(pk__isnull=True))
        )
    ).order_by('name')

    selected_category = None
    datasets = []

    if category_id:
        selected_category = get_object_or_404(Category, pk=category_id)
        if request.user.is_authenticated:
            qs = Dataset.objects.filter(
                category=selected_category
            ).filter(Q(is_public=True) | Q(owner=request.user))
        else:
            qs = Dataset.objects.filter(category=selected_category, is_public=True)
        
        datasets = qs.select_related('owner').order_by('-created_at')

    context = {
        'categories': categories,
        'selected_category': selected_category,
        'datasets': datasets,
    }
    return render(request, 'datasets/categories.html', context)
