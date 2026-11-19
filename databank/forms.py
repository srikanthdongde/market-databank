from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Dataset, Category, UserProfile
from .utils import validate_csv_file


class UserRegisterForm(UserCreationForm):
    """
    Registration form with email, full name, and customized Bootstrap styling.
    """
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Alex'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Kumar'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'alex.kumar@university.edu'})
    )
    organization = forms.CharField(
        max_length=150,
        required=False,
        initial='Department of Computer Science / Economics',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'University or Organization name'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a unique username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email


class UserLoginForm(AuthenticationForm):
    """
    Standard login form with Bootstrap 5 input classes and placeholders.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or Email', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )


class UserProfileForm(forms.ModelForm):
    """
    Form to update student/researcher profile details.
    """
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserProfile
        fields = ['organization', 'bio']
        widgets = {
            'organization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. National Institute of Technology'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your research focus or data interests...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email


class DatasetForm(forms.ModelForm):
    """
    Form for uploading a new market dataset with CSV file validation.
    """
    class Meta:
        model = Dataset
        fields = ['title', 'category', 'description', 'source', 'uploaded_file', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. NIFTY 50 Historical Daily Prices (2020-2024)'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide comprehensive context: data collection methodology, column explanations, time window, frequency, etc.'
            }),
            'source': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. National Stock Exchange (NSE) / Kaggle Open Data'
            }),
            'uploaded_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.csv'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch'
            }),
        }

    def clean_uploaded_file(self):
        file = self.cleaned_data.get('uploaded_file')
        if not file:
            raise forms.ValidationError("Please select a valid CSV file to upload.")

        is_valid, error_msg, metadata = validate_csv_file(file)
        if not is_valid:
            raise forms.ValidationError(error_msg)

        # Store parsed metadata on the form instance for the view to save
        self.parsed_metadata = metadata
        return file


class DatasetEditForm(forms.ModelForm):
    """
    Form for updating an existing dataset.
    The file upload is optional: if omitted, the existing file is preserved.
    """
    uploaded_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'}),
        help_text="Optional: Leave blank to retain current CSV file, or choose a new CSV to replace it."
    )

    class Meta:
        model = Dataset
        fields = ['title', 'category', 'description', 'source', 'uploaded_file', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }

    def clean_uploaded_file(self):
        file = self.cleaned_data.get('uploaded_file')
        if file:
            is_valid, error_msg, metadata = validate_csv_file(file)
            if not is_valid:
                raise forms.ValidationError(error_msg)
            self.parsed_metadata = metadata
        else:
            self.parsed_metadata = None
        return file
