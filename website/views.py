from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .adapters import notify_access_request
from .forms import AdminSignupForm, ChatForm, ContactForm, OfferForm
from .models import APPRAISAL_DISTRICTS, Deal, DealInProgress, Property, Review, TrustProfile

PRICE_FILTERS = [300000, 400000, 500000, 600000]


def published_homes():
    return Property.objects.filter(is_published=True).prefetch_related('photos')


def home(request):
    return render(request, 'website/home.html', {
        'featured': published_homes().exclude(status=Property.Status.SOLD)[:3],
        'latest_deal': Deal.objects.first(),
    })


def homes_list(request):
    homes = published_homes()
    q = request.GET
    price, beds, city, status = q.get('price', ''), q.get('beds', ''), q.get('location', ''), q.get('status', '')
    if price.isdigit():
        homes = homes.filter(price__lte=int(price))
    if beds.isdigit():
        homes = homes.filter(beds__gte=int(beds))
    if city:
        homes = homes.filter(city=city.split(',')[0].strip())
    if status in Property.Status.values:
        homes = homes.filter(status=status)
    locations = sorted({p.location for p in published_homes()})
    return render(request, 'website/homes_list.html', {
        'homes': homes,
        'total': published_homes().count(),
        'locations': locations,
        'price_options': PRICE_FILTERS,
        'statuses': Property.Status.choices,
        'f': {'price': price, 'beds': beds, 'location': city, 'status': status},
        'filtered': any([price, beds, city, status]),
    })


def home_detail(request, slug):
    home = get_object_or_404(published_homes(), slug=slug)
    more = published_homes().exclude(pk=home.pk).exclude(status=Property.Status.SOLD)[:3]
    return render(request, 'website/home_detail.html', {'home': home, 'more': more, 'comps': home.comparables.all()})


def make_offer(request, slug):
    home = get_object_or_404(published_homes().exclude(status=Property.Status.SOLD), slug=slug)
    if request.method == 'POST':
        form = OfferForm(request.POST, home=home)
        if form.is_valid():
            if not form.is_spam():
                offer = form.save()
                if settings.CONTACT_NOTIFY_EMAIL:
                    send_mail(
                        f'Offer request: ${offer.offer_price:,} on {offer.home_label}',
                        f'{offer.name} <{offer.email}> {offer.phone}\n'
                        f'Offer: ${offer.offer_price:,} (asking ${offer.listed_price:,})\n'
                        f'Paying: {offer.get_financing_display()} {offer.lender}\n'
                        f'Close: {offer.get_timeline_display()}\n'
                        f'Showing first: {"yes" if offer.wants_showing else "no"}\n'
                        f'Agent: {offer.agent_name or "none"}\n\n{offer.notes}',
                        settings.DEFAULT_FROM_EMAIL, [settings.CONTACT_NOTIFY_EMAIL], fail_silently=True)
            return render(request, 'website/offer_sent.html', {'home': home})
    else:
        form = OfferForm(home=home, initial={'wants_showing': True})
    return render(request, 'website/offer.html', {'home': home, 'form': form})


def how_it_works(request):
    return render(request, 'website/how_it_works.html')


def past_deals(request):
    return render(request, 'website/past_deals.html', {'deals': Deal.objects.all()})


def in_progress(request):
    return render(request, 'website/in_progress.html', {
        'projects': DealInProgress.objects.filter(is_published=True)})


def verify(request):
    return render(request, 'website/verify.html', {
        'profile': TrustProfile.load(),
        'reviews': Review.objects.filter(is_approved=True),
        'districts': sorted(APPRAISAL_DISTRICTS.items()),
    })


def map_page(request):
    homes = published_homes().filter(latitude__isnull=False, longitude__isnull=False)
    pins = []
    for h in homes:
        cover = h.cover
        pins.append({
            'slug': h.slug, 'address': h.address, 'location': h.location, 'url': h.get_absolute_url(),
            'price': h.price, 'nearby': h.nearby_price, 'savings': h.savings,
            'status': h.status, 'status_label': h.get_status_display(),
            'beds': h.beds, 'baths': float(h.baths), 'sqft': h.sqft,
            'lat': float(h.latitude), 'lng': float(h.longitude),
            'photo': cover.card_url() if cover else '',
        })
    return render(request, 'website/map.html', {'pins': pins, 'homes': homes, 'statuses': Property.Status.choices})


def about(request):
    return render(request, 'website/about.html')


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            if not form.is_spam():
                msg = form.save()
                if settings.CONTACT_NOTIFY_EMAIL:
                    send_mail(
                        f'New message from {msg.name}',
                        f'{msg.name} <{msg.email}> {msg.phone}\nHome: {msg.home or "-"}\n\n{msg.message}',
                        settings.DEFAULT_FROM_EMAIL, [settings.CONTACT_NOTIFY_EMAIL], fail_silently=True)
            messages.success(request, 'Thank you! Your message was sent. I will reply soon.')
            return redirect(reverse('website:contact') + '#contact-form')
    else:
        initial = {}
        slug = request.GET.get('home')
        if slug:
            home = published_homes().filter(slug=slug).first()
            if home:
                initial = {'home': f'{home.address}, {home.location}',
                           'message': f'Hi, I am interested in {home.address}. Could you tell me more or set up a showing?'}
        form = ContactForm(initial=initial)
    return render(request, 'website/contact.html', {'form': form})


@require_POST
def chat_message(request):
    """Messages from the chat bubble. Returns JSON for the widget."""
    form = ChatForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'ok': False, 'errors': {k: [str(e) for e in v] for k, v in form.errors.items()}}, status=400)
    if not form.is_spam():
        msg = form.save()
        if settings.CONTACT_NOTIFY_EMAIL:
            send_mail(f'New chat message from {msg.name}', f'{msg.name} <{msg.email}>\n\n{msg.message}',
                      settings.DEFAULT_FROM_EMAIL, [settings.CONTACT_NOTIFY_EMAIL], fail_silently=True)
    return JsonResponse({'ok': True})


def legal(template):
    def view(request):
        return render(request, f'website/{template}.html')
    view.__name__ = template
    return view


@require_GET
def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse('django.contrib.sitemaps.views.sitemap'))
    return HttpResponse(f'User-agent: *\nDisallow: /\n\nSitemap: {sitemap_url}\n', content_type='text/plain')


@require_GET
def favicon(request):
    # Resolved per request so it follows the versioned file name in production.
    return redirect(static('website/favicon.ico'))


def admin_signup(request):
    """Sign-up page styled like the admin login. Accounts wait for the owner to approve them."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin:index')
    if request.method == 'POST':
        form = AdminSignupForm(request.POST)
        if form.is_valid():
            if not form.is_spam():
                notify_access_request(form.save())
            return render(request, 'admin/signup.html', {'submitted': True})
    else:
        form = AdminSignupForm()
    return render(request, 'admin/signup.html', {'form': form})
