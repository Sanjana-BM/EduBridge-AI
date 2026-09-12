from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.user_login, name='login'),
    path('standalone-login/', views.standalone_login, name='standalone_login'),  # For direct access
    path('logout/', views.user_logout, name='logout'),
    path('student/register/', views.student_register, name='student_register'),
    
    # Dashboard URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    
    # Teacher URLs
    path('teacher/add-material/', views.add_study_material, name='add_study_material'),
    path('teacher/add-faq/', views.add_faq, name='add_faq'),
    path('teacher/analytics/', views.teacher_analytics, name='teacher_analytics'),
    path('api/study-materials/<int:material_id>/view/', views.view_study_material, name='view_study_material'),
    path('api/study-materials/<int:material_id>/download/', views.download_study_material, name='download_study_material'),

    # Chat API
    path('api/chat/', views.chat_with_ai, name='chat_with_ai'),
    path('api/faqs/', views.get_faqs, name='get_faqs'),
    path('api/study-materials/', views.get_study_materials, name='get_study_materials'),
    # path('api/study-materials/<int:material_id>/download/', views.download_material, name='download_material'),
    path('api/study-materials/<int:material_id>/view/', views.get_study_materials, name='view_material'),
    
]