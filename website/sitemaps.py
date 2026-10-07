from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Property


class PageSitemap(Sitemap):
    changefreq = 'weekly'

    def items(self):
        return ['home', 'homes', 'map', 'how_it_works', 'past_deals', 'in_progress', 'about', 'verify', 'contact',
                'privacy', 'terms', 'accessibility']

    def location(self, item):
        return reverse(f'website:{item}')

    def priority(self, item):
        return 1.0 if item in ('home', 'homes') else 0.3 if item in ('privacy', 'terms', 'accessibility') else 0.6


class PropertySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Property.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.created


sitemaps = {'pages': PageSitemap, 'homes': PropertySitemap}
