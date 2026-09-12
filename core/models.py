from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class CustomUser(AbstractUser):
    # Add related_name to avoid clashes with default User model
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='customuser_set',  # Changed related_name
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',  # Changed related_name
        related_query_name='user',
    )
    
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    syllabus = models.TextField(blank=True, help_text="Detailed syllabus for this subject")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Class(models.Model):
    name = models.CharField(max_length=50)
    section = models.CharField(max_length=10, blank=True)
    subjects = models.ManyToManyField(Subject)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.section}" if self.section else self.name

class TeacherProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    qualification = models.CharField(max_length=100)
    experience = models.IntegerField(default=0)
    subjects = models.ManyToManyField(Subject)
    classes = models.ManyToManyField(Class)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    class_enrolled = models.ForeignKey(Class, on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    parent_phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.roll_number}"

class StudyMaterial(models.Model):
    MATERIAL_TYPE_CHOICES = (
        ('notes', 'Notes'),
        ('video', 'Video'),
        ('assignment', 'Assignment'),
        ('quiz', 'Quiz'),
        ('formula', 'Formula'),
        ('example', 'Example'),
        ('theory', 'Theory'),
        ('pdf', 'PDF'),
        ('document', 'Document'),
        ('link', 'Link'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPE_CHOICES)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)
    file = models.FileField(upload_to='study_materials/', blank=True, null=True)
    external_url = models.URLField(blank=True)  # Changed from 'url' to match your view
    content = models.TextField(blank=True, help_text="Detailed content that AI can use for answering questions")
    keywords = models.TextField(blank=True, help_text="Comma-separated keywords for better search")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Add these missing fields
    is_published = models.BooleanField(default=True)
    file_size = models.IntegerField(default=0, help_text="File size in bytes")
    class_level = models.ForeignKey('Class', on_delete=models.CASCADE, null=True, blank=True)  # Add this field
    
    def save(self, *args, **kwargs):
        # Calculate file size if file exists
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

class FAQ(models.Model):
    question = models.TextField()
    answer = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)
    keywords = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FAQ: {self.question[:50]}..."

class ChatHistory(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    confidence_score = models.FloatField(default=0.0)
    source_material = models.ForeignKey(StudyMaterial, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q: {self.question[:50]}..."