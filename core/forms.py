from django import forms
from .models import *
import re

class CustomUserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Create a strong password'
        }),
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'phone']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Choose a username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'your.email@example.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter your last name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '+91 98765 43210'
            }),
        }
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose a different one.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['class_enrolled', 'roll_number', 'date_of_birth', 'parent_phone']
        widgets = {
            'class_enrolled': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent'
            }),
            'roll_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': 'Enter your roll number'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'type': 'date'
            }),
            'parent_phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': '+91 98765 43210'
            }),
        }
    
    def clean_roll_number(self):
        roll_number = self.cleaned_data['roll_number']
        if StudentProfile.objects.filter(roll_number=roll_number).exists():
            raise forms.ValidationError("This roll number is already registered.")
        return roll_number
class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['class_enrolled', 'roll_number', 'date_of_birth', 'parent_phone']


class StudyMaterialForm(forms.ModelForm):
    class Meta:
        model = StudyMaterial
        fields = ['title', 'description', 'material_type', 'subject', 'content', 'keywords', 'file', 'external_url']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Detailed content that AI will use to answer student questions'}),
            'keywords': forms.TextInput(attrs={'placeholder': 'Comma-separated keywords for better search'}),
            'external_url': forms.URLInput(attrs={'placeholder': 'https://example.com'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help texts
        self.fields['external_url'].help_text = 'Optional: External URL for the study material'
        self.fields['file'].help_text = 'Optional: Upload a file'
        self.fields['content'].help_text = 'This content will be used by AI to answer student questions'
        
class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ['question', 'answer', 'subject', 'keywords']
        widgets = {
            'question': forms.Textarea(attrs={'rows': 3}),
            'answer': forms.Textarea(attrs={'rows': 5}),
            'keywords': forms.TextInput(attrs={'placeholder': 'Comma-separated keywords'}),
        }