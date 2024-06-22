from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/editprofile/', views.edit_student, name='editprofile'),
    path('dashboard/inoutdorm/', views.inoutdorm, name='inoutdorm'),
    path('dashboard/repair/', views.repair, name='repair'),
    path('dashboard/visit/', views.visit, name='visit'),
    path('dashboard/repair/delete/<int:repair_id>/', views.delete_repair, name='delete_repair'),
    path('dashboard/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/dormmanager/', views.dormmanager, name='dormmanager'),
    path('dashboard/dormmanager/<str:dormmanager_id>/', views.edit_dormmanager, name='edit_dormmanager'),
    path('dashboard/dormmanager/delete_dm/<str:dormmanager_id>/', views.delete_dormmanager, name='delete_dormmanager'),
    path('dashboard/dormbuilding/', views.dormbuilding, name='dormbuilding'),
    path('dashboard/dormbuilding/dorm', views.dorm, name='dorm'),
    path('dashboard/dormbuilding/delete_bd/<int:id>', views.deletebuilding, name='deletebuilding'),
    path('dashboard/dormbuilding/delete_dm/<int:id>', views.deletedorm, name='deletedorm'),
    path('dashboard/student/', views.student, name='student'),
    path('dashboard/student/<str:stu_id>/', views.delete_student, name='delete_student'),
    path('dashboard/student/dormchange/<str:id>/', views.dorm_change, name='dorm_change'),
    path('dashboard/inoutdorm/in/<str:applicant_id>/', views.apply_in, name='apply_in'),
    path('dashboard/inoutdorm/<int:apply_id>/', views.apply_denied, name='apply_denied'),
    path('dashboard/inoutdorm/out/<str:applicant_id_out>/', views.apply_out, name='apply_out'),
    path('dashboard/repair/completed/<int:repair_id>/', views.repair_complete, name='repair_completed'),
    path('dashboard/visit/ac/<int:id>/',views.visit_ac, name='visit_ac'),
    path('dashboard/visit/dn/<int:id>/', views.visit_dn, name='visit_dn'),
    path('dashboard/editprofile/img_upload/', views.image_upload, name='image_upload'),
]
