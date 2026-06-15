from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('countries/', views.country_hub_view, name='country_hub'),
    path('countries/<slug:slug>/', views.country_detail_view, name='country_detail'),
    path('features/', views.features_view, name='features'),
    path('platform/', views.platform_view, name='platform'),
    path('security/', views.security_view, name='security'),
    path('demo/thankyou/', views.demo_thankyou_view, name='demo_thankyou'),
    path('demo/', views.demo_view, name='demo'),
    path('demo-request/', views.demo_request_view, name='demo_request'),





    path('articles/br/overview/1/', views.brazil_article_0001, name='brazil_article_0001'),
    path('articles/br/overview/2/', views.brazil_article_detail_view, {"article_id": 2}, name='brazil_article_0002'),
    path('articles/br/overview/3/', views.brazil_article_detail_view, {"article_id": 3}, name='brazil_article_0003'),
    path('articles/br/overview/4/', views.brazil_article_detail_view, {"article_id": 4}, name='brazil_article_0004'),
    path('articles/br/overview/5/', views.brazil_article_detail_view, {"article_id": 5}, name='brazil_article_0005'),
    path('resources/chile-payroll-guide/', views.chile_article_0001, name='chile_article_0001'),
    path('resources/costa-rica-payroll-guide/', views.costa_rica_article_0001, name='costa_rica_article_0001'),





]
