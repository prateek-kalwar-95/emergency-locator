from django.urls import path
from locator import views

app_name = 'locator'

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_dataset, name='upload_dataset'),
    path('incidents/', views.list_incidents, name='list_incidents'),
    path('units/', views.list_units, name='list_units'),
    path('find-nearest/', views.find_nearest, name='find_nearest'),
]
