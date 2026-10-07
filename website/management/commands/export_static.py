import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import Client, override_settings
from django.urls import reverse, set_script_prefix

from website.models import Property

PAGES = ['home', 'homes', 'map', 'how_it_works', 'past_deals', 'in_progress', 'about', 'verify',
         'contact', 'privacy', 'terms', 'accessibility']


class Command(BaseCommand):
    help = 'Render the public pages to plain HTML for a static host such as GitHub Pages.'

    def add_arguments(self, parser):
        parser.add_argument('out', help='Folder to write the site into (its contents are replaced).')
        parser.add_argument('--base', default='/', help='URL path the site is served from, e.g. /thistledown/')
        parser.add_argument('--domain', default='', help='Site origin for canonical links, e.g. https://name.github.io')

    def handle(self, out, base, domain, **opts):
        base = '/' + base.strip('/') + '/' if base.strip('/') else '/'
        out = Path(out).resolve()
        if out.exists() and not (out / 'index.html').exists() and any(out.iterdir()):
            raise CommandError(f'{out} is not empty and does not look like a previous export.')
        shutil.rmtree(out, ignore_errors=True)
        site_info = {**settings.SITE_INFO, 'domain': domain.rstrip('/') or settings.SITE_INFO['domain']}
        storages = {**settings.STORAGES,
                    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}}
        with override_settings(FORCE_SCRIPT_NAME=base.rstrip('/') or None, STATIC_URL=f'{base}static/',
                               STORAGES=storages, SITE_INFO=site_info, ALLOWED_HOSTS=['*']):
            set_script_prefix('/')  # paths below are relative to the site root
            urls = [reverse(f'website:{name}') for name in PAGES]
            for home in Property.objects.filter(is_published=True):
                urls.append(reverse('website:home_detail', args=[home.slug]))
                if home.status != Property.Status.SOLD:
                    urls.append(reverse('website:make_offer', args=[home.slug]))
            set_script_prefix(base)  # the test client does not set it, and {% url %} needs it
            client = Client()
            demo_js = f'<script src="{base}static/website/js/static-demo.js" defer></script>\n</head>'
            for url in urls:
                res = client.get(url)
                if res.status_code != 200:
                    raise CommandError(f'{url} returned {res.status_code}')
                html = res.content.decode().replace('</head>', demo_js, 1)
                path = out / url.lstrip('/') / 'index.html'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(html, encoding='utf-8')
        shutil.copytree(Path(settings.BASE_DIR) / 'website' / 'static', out / 'static')
        self.stdout.write(self.style.SUCCESS(f'Wrote {len(urls)} pages to {out}'))
