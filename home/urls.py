from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('features/', views.features_view, name='features'),
    path('platform/', views.platform_view, name='platform'),
    path('security/', views.security_view, name='security'),
    path('pricing/', views.pricing_view, name='pricing'),
    path('demo/', views.demo_view, name='demo'),

    # This URL catches the form submission
    path('demo-request/', views.demo_request_view, name='demo_request'),





    path('articles/br/overview/', views.brazil_article_0001, name='brazil_article_0001'),
    path('articles/cl/overview/', views.chile_article_0001, name='chile_article_0001'),
]