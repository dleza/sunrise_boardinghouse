from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="dashboard"),
    path("rooms/", views.rooms_list, name="dash_rooms"),
    path("students/", views.students_list, name="dash_students"),
    path("invoices/", views.invoices_list, name="dash_invoices"),
    path("payments/", views.payments_list, name="dash_payments"),
    path("expenses/", views.expenses_list, name="dash_expenses"),
    path("maintenance/", views.maintenance_list, name="dash_maintenance"),
    path("reports/", views.reports, name="dash_reports"),
    path("website/gallery/", views.gallery_manager, name="dash_gallery_manager"),
    path("website/blog/", views.blog_manager, name="dash_blog_manager"),
    path("website/contact/", views.contact_manager, name="dash_contact_manager"),
    path("occupancy/", views.occupancy_assign, name="dash_occupancy"),
    path("occupancy/<int:occ_id>/exit/", views.occupancy_exit, name="dash_occupancy_exit"),
    path("occupancy/<int:occ_id>/transfer/", views.occupancy_transfer, name="dash_occupancy_transfer"),
    path("occupancy/<int:occ_id>/exit/", views.occupancy_exit, name="dash_occupancy_exit"),
    path("occupancy/<int:occ_id>/transfer/", views.occupancy_transfer, name="dash_occupancy_transfer"),
    path("maintenance/<int:req_id>/update/", views.maintenance_update, name="dash_maintenance_update"),
    path("reports/maintenance/", views.maintenance_reports, name="dash_maintenance_reports"),
    path("reports/finance/", views.finance_reports, name="dash_finance_reports"),
    path("billing/generate-invoices/", views.generate_invoices, name="dash_generate_invoices"),
    path("reports/", views.reports_home, name="reports_home"),
    path("reports/rent/", views.rent_report, name="rent_report"),
    path("reports/expenses/", views.expenses_report, name="expenses_report"),
    path("reports/profit/", views.profit_report, name="profit_report"),

]