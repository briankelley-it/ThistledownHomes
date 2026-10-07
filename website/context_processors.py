from django.conf import settings

# Main navigation, shared by the header, mobile menu, and footer.
NAV = [
    ('website:homes', 'Homes For Sale'),
    ('website:map', 'Map'),
    ('website:how_it_works', 'How It Works'),
    ('website:past_deals', 'Past Deals'),
    ('website:in_progress', 'Deals In Progress'),
    ('website:about', 'About'),
    ('website:verify', 'Verify Me'),
]


def site(request):
    match = getattr(request, 'resolver_match', None)
    current = f'{match.namespace}:{match.url_name}' if match and match.namespace else ''
    if current == 'website:home_detail':
        current = 'website:homes'
    # brand_name survives views (like the admin login) that pass their own `site`.
    return {'site': settings.SITE_INFO, 'brand_name': settings.SITE_INFO['name'],
            'google_login_enabled': bool(settings.GOOGLE_CLIENT_ID),
            'google_setup_hint': settings.DEBUG and not settings.GOOGLE_CLIENT_ID, 'nav': NAV, 'current_page': current}
