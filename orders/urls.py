from django.urls import path
from . import views
urlpatterns = [
    path('place_order', views.place_order, name='place_order'),
    path('payments', views.payments, name='payments'),
    path('order_complete', views.order_complete, name='order_complete'),
    path('order_complete/<int:order_id>', views.order_complete, name='order_complete'),
    path('order_complete/<int:order_id>/<int:payment_id>', views.order_complete, name='order_complete'),
    path('order_complete/<int:order_id>/<int:payment_id>/<int:status>', views.order_complete, name='order_complete'),
]