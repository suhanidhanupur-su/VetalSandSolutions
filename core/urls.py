from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('industries/', views.industries, name='industries'),
    path('applications/', views.applications, name='applications'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('gallery/', views.gallery, name='gallery'),
]