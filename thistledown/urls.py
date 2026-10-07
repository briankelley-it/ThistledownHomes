from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import RedirectView

from website.sitemaps import sitemaps
from website.views import admin_signup, favicon, robots_txt

admin.site.site_header = 'Thistledown Homes admin'
admin.site.site_title = 'Thistledown Homes admin'
admin.site.index_title = 'Manage homes, deals, and messages'

urlpatterns = [
    path('admin/signup/', admin_signup, name='admin_signup'),
    path('admin/', admin.site.urls),
    # Google sign-in (callback lives at /accounts/google/login/callback/).
    # Send allauth's plain login and signup pages to the custom ones above.
    path('accounts/login/', RedirectView.as_view(pattern_name='admin:login', query_string=True)),
    path('accounts/signup/', RedirectView.as_view(pattern_name='admin_signup')),
    path('accounts/', include('allauth.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots'),
    # Browsers and the admin request /favicon.ico directly.
    path('favicon.ico', favicon),
    path('', include('website.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
