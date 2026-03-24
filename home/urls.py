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





    path('articles/br/overview/1', views.brazil_article_0001, name='brazil_article_0001'),
    path('articles/br/overview/2', views.brazil_article_0002, name='brazil_article_0002'),
    path('articles/br/overview/3', views.brazil_article_0003, name='brazil_article_0003'),
    path('articles/br/overview/4', views.brazil_article_0004, name='brazil_article_0004'),
    path('articles/br/overview/5', views.brazil_article_0005, name='brazil_article_0005');





]