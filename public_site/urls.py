from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('rooms/', views.rooms, name="rooms"),
    path('gallery/', views.gallery, name="gallery"),
    path('features/', views.features, name="features"),
    path('tips/', views.tips_list, name="tips_list"),
    path('tips/<slug:slug>/', views.tips_detail, name="tips_detail"),
    path('contact/', views.contact, name="contact"),
]