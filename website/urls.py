from django.urls import path

from . import views

app_name = 'website'

urlpatterns = [
    path('', views.home, name='home'),
    path('homes/', views.homes_list, name='homes'),
    path('homes/<slug:slug>/', views.home_detail, name='home_detail'),
    path('homes/<slug:slug>/offer/', views.make_offer, name='make_offer'),
    path('map/', views.map_page, name='map'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('past-deals/', views.past_deals, name='past_deals'),
    path('deals-in-progress/', views.in_progress, name='in_progress'),
    path('about/', views.about, name='about'),
    path('verify/', views.verify, name='verify'),
    path('contact/', views.contact, name='contact'),
    path('chat/', views.chat_message, name='chat'),
    path('privacy/', views.legal('privacy'), name='privacy'),
    path('terms/', views.legal('terms'), name='terms'),
    path('accessibility/', views.legal('accessibility'), name='accessibility'),
]
