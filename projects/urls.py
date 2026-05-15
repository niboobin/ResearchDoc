from django.urls import path

from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('projects/new/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),

    path('projects/<int:project_pk>/resources/new/', views.resource_create, name='resource_create'),
    path('resources/<int:pk>/edit/', views.resource_edit, name='resource_edit'),
    path('resources/<int:pk>/delete/', views.resource_delete, name='resource_delete'),
    path('resources/<int:pk>/generate/', views.resource_generate_annotation, name='resource_generate_annotation'),

    path('projects/<int:project_pk>/summaries/new/', views.summary_create, name='summary_create'),
    path('summaries/<int:pk>/edit/', views.summary_edit, name='summary_edit'),
    path('summaries/<int:pk>/delete/', views.summary_delete, name='summary_delete'),

    path('projects/<int:project_pk>/comparisons/new/', views.comparison_create, name='comparison_create'),
    path('comparisons/<int:pk>/edit/', views.comparison_edit, name='comparison_edit'),
    path('comparisons/<int:pk>/delete/', views.comparison_delete, name='comparison_delete'),

    path('search/', views.search, name='search'),
]
