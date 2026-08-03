from django.urls import path
from . import views
from .flexpay_integration import (
    initiate_subscription_payment,
    initiate_summary_purchase,
    flexpay_callback,
    create_subscription_after_payment
)

urlpatterns = [
    path('purchases/', views.PurchaseListCreateView.as_view(), name='purchase-list-create'),
    path('purchases/<int:pk>/', views.PurchaseDetailView.as_view(), name='purchase-detail'),
    path('purchases/<int:purchase_id>/complete/', views.complete_purchase, name='complete-purchase'),
    path('purchases/initiate/', views.initiate_purchase, name='initiate-purchase'),
    path('purchases/check-status/<str:transaction_ref>/', views.check_purchase_status, name='check-purchase-status'),
    path('simulate-payment/', views.simulate_payment, name='simulate-payment'),

    # Services endpoints
    path('services/', views.ServiceListCreateView.as_view(), name='service-list-create'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service-detail'),

    # Abonnements endpoints
    path('abonnements/', views.AbonnementListCreateView.as_view(), name='abonnement-list-create'),
    path('abonnements/<int:pk>/', views.AbonnementDetailView.as_view(), name='abonnement-detail'),
    path('abonnements/check-status/', views.check_subscription_status, name='check-subscription-status'),
    path('abonnements/initiate-payment/', views.initiate_subscription_payment_view, name='initiate-subscription-payment-view'),

    # FlexPay Integration
    path('initiate-subscription-payment/', initiate_subscription_payment, name='initiate-subscription-payment'),
    path('initiate-summary-purchase/', initiate_summary_purchase, name='initiate-summary-purchase'),
    path('create-subscription-after-payment/', create_subscription_after_payment, name='create-subscription-after-payment'),
    path('flexpay-callback/', flexpay_callback, name='flexpay-callback'),
]
