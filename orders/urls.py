from django.urls import path

from . import views


urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('orders/<int:order_id>/success/', views.order_success, name='order_success'),
    path('account/orders/', views.order_list, name='order_list'),
    path('account/orders/<int:order_id>/', views.order_detail, name='order_detail'),
]