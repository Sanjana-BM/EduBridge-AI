from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import (
    CustomUser, Subject, TeacherProfile, Class, 
    StudyMaterial, FAQ, ChatHistory, StudentProfile
)


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'user_type', 'phone', 'address', 'first_name', 'last_name')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = '__all__'


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'is_staff', 'created_at')
    list_filter = ('user_type', 'is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    readonly_fields = ('last_login', 'date_joined', 'created_at')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Custom Fields'), {'fields': ('user_type', 'phone', 'address')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'user_type'),
        }),
        (_('Personal info'), {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'phone', 'address'),
        }),
    )


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'code')
    ordering = ('name',)
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('name', 'code')
        }),
        (_('Description'), {
            'fields': ('description', 'syllabus'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'qualification', 'experience', 'is_active')
    list_filter = ('is_active', 'qualification')
    filter_horizontal = ('subjects', 'classes')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'qualification')
    fieldsets = (
        (None, {
            'fields': ('user', 'qualification', 'experience', 'is_active')
        }),
        (_('Associations'), {
            'fields': ('subjects', 'classes')
        }),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'roll_number', 'class_enrolled', 'date_of_birth')
    list_filter = ('class_enrolled', 'date_of_birth')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'roll_number', 'parent_phone')
    fieldsets = (
        (None, {
            'fields': ('user', 'roll_number', 'class_enrolled')
        }),
        (_('Personal Information'), {
            'fields': ('date_of_birth', 'parent_phone'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'created_at')
    list_filter = ('created_at',)
    filter_horizontal = ('subjects',)
    search_fields = ('name', 'section')
    ordering = ('name', 'section')
    readonly_fields = ('created_at',)


@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'material_type', 'subject', 'teacher', 'class_level', 'is_published', 'created_at')
    list_filter = ('material_type', 'subject', 'teacher', 'class_level', 'is_published', 'created_at')
    search_fields = ('title', 'description', 'content', 'keywords')
    readonly_fields = ('created_at', 'file_size')
    list_editable = ('is_published',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'material_type', 'subject', 'teacher', 'class_level', 'is_published')
        }),
        (_('Content'), {
            'fields': ('description', 'content', 'file', 'external_url')
        }),
        (_('Metadata'), {
            'fields': ('keywords', 'file_size', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'subject', 'teacher', 'created_at')
    list_filter = ('subject', 'teacher', 'created_at')
    search_fields = ('question', 'answer', 'keywords')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('question', 'subject', 'teacher')
        }),
        (_('Answer'), {
            'fields': ('answer',)
        }),
        (_('Metadata'), {
            'fields': ('keywords', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'confidence_score', 'created_at')
    list_filter = ('subject', 'confidence_score', 'created_at')
    search_fields = ('student__user__username', 'student__user__first_name', 'student__user__last_name', 'question', 'answer')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('student', 'subject', 'confidence_score', 'source_material')
        }),
        (_('Chat Content'), {
            'fields': ('question', 'answer')
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Typically chat history is auto-generated, so disable adding manually
        return False
    
    def has_change_permission(self, request, obj=None):
        # Typically chat history should not be editable
        return False