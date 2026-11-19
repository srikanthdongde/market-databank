from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..forms import UserRegisterForm, UserLoginForm, UserProfileForm
from ..models import Dataset


def register_view(request):
    """
    Handle new student/researcher account registration.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Update organization from form on the user profile
            org = form.cleaned_data.get('organization')
            if org and hasattr(user, 'profile'):
                user.profile.organization = org
                user.profile.save()

            login(request, user)
            messages.success(request, f"Welcome to Market Databank, {user.first_name or user.username}! Your account has been registered.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors in the registration form.")
    else:
        form = UserRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    Handle user login with session initialization.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """
    Log out the current authenticated user.
    """
    logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('login')


@login_required
def profile_view(request):
    """
    Display and edit user profile information and user upload activity statistics.
    """
    user = request.user
    user_datasets = Dataset.objects.filter(owner=user)
    
    total_uploads = user_datasets.count()
    public_uploads = user_datasets.filter(is_public=True).count()
    private_uploads = user_datasets.filter(is_public=False).count()
    total_downloads = sum(d.download_count for d in user_datasets)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user.profile, user=user)
        if form.is_valid():
            # Update User model fields
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            # Update Profile fields
            form.save()
            messages.success(request, "Your profile information has been updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "Please fix the errors in your profile form.")
    else:
        form = UserProfileForm(instance=user.profile, user=user)

    context = {
        'form': form,
        'total_uploads': total_uploads,
        'public_uploads': public_uploads,
        'private_uploads': private_uploads,
        'total_downloads': total_downloads,
        'recent_datasets': user_datasets[:5],
    }
    return render(request, 'accounts/profile.html', context)
