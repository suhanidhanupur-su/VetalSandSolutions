from django.urls import path

from . import views


urlpatterns = [
    path('orders/<int:order_id>/razorpay/create/', views.create_razorpay_order, name='create_razorpay_order'),
    path('orders/<int:order_id>/razorpay/verify/', views.verify_payment, name='verify_payment'),
    path('orders/<int:order_id>/payment-failed/', views.payment_failed, name='payment_failed'),
]