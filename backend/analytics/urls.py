from django.urls import path

from . import views

urlpatterns = [
    path('admin/statistics/overview/', views.OverviewStatsView.as_view(),
         name='admin-statistics-overview'),
    path('admin/statistics/users/', views.UsersStatsView.as_view(),
         name='admin-statistics-users'),
    path('admin/statistics/summaries/', views.SummariesStatsView.as_view(),
         name='admin-statistics-summaries'),
    path('admin/statistics/qcm/', views.QcmStatsView.as_view(),
         name='admin-statistics-qcm'),
    path('admin/statistics/transactions/', views.TransactionsStatsView.as_view(),
         name='admin-statistics-transactions'),
    path('admin/statistics/purchases/', views.PurchasesStatsView.as_view(),
         name='admin-statistics-purchases'),
    path('admin/statistics/subscriptions/', views.SubscriptionsStatsView.as_view(),
         name='admin-statistics-subscriptions'),
    path('admin/statistics/revenue/', views.RevenueStatsView.as_view(),
         name='admin-statistics-revenue'),
    path('admin/statistics/export/excel/', views.ExportExcelView.as_view(),
         name='admin-statistics-export-excel'),
    path('admin/statistics/export/csv/', views.ExportCsvView.as_view(),
         name='admin-statistics-export-csv'),
]
