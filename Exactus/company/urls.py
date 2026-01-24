from django.urls import path
from Exactus.company import views

app_name = "companies"

urlpatterns = [
    # ────────────────────────────────────────────────
    # Global/Admin Routes (Must come first)
    # ────────────────────────────────────────────────
    path("company/upload/", views.company_upload_view, name="company_upload_global"),
    path("company/upload/result/", views.company_upload_result_view, name="company_upload_result_global"),
    path("company/upload/template/", views.download_companies_template, name="download_companies_template_global"),

    # ────────────────────────────────────────────────
    # Country-Specific Routes
    # ────────────────────────────────────────────────
    path("<slug:country_slug>/upload/", views.company_upload_view, name="company_upload"),
    path("<slug:country_slug>/upload/result/", views.company_upload_result_view, name="company_upload_result"),
    path("<slug:country_slug>/upload/template/", views.download_companies_template, name="download_companies_template"),

    # ────────────────────────────────────────────────
    # CRUD Routes
    # ────────────────────────────────────────────────
    path("<slug:country_slug>/", views.company, name="company"),
    path("<slug:country_slug>/create/", views.company_create, name="company_create"),
    path("<slug:country_slug>/delete/", views.company_delete, name="company_delete"),
    path("<slug:country_slug>/edit/<int:company_id>/", views.company_edit, name="company_edit"),


    path('<slug:country_slug>/test-validation/', views.company_test_validation,name='company_test_validation'),
    path('<slug:country_slug>/create/debug/',views.company_form_debug, name='company_form_debug'),
    path('<slug:country_slug>/debug-info/',views.company_debug_info,name='company_debug_info'),
    path('<slug:country_slug>/validate-ajax/',views.company_validate_ajax, name='company_validate_ajax'),
    path('<slug:country_slug>/field-requirements/',views.company_field_requirements,name='company_field_requirements'),

    path('<slug:country_slug>/groups/', views.client_group_list, name='client_group_list'),
    path('<slug:country_slug>/groups/create/', views.client_group_create, name='client_group_create'),
    path('<slug:country_slug>/groups/<int:group_id>/edit/', views.client_group_edit, name='client_group_edit'),

]