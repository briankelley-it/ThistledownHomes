from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from .models import ContactMessage, Deal, Property, Review, TrustProfile


class PageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)

    def test_every_page_loads(self):
        for name in ['home', 'homes', 'how_it_works', 'past_deals', 'in_progress', 'about', 'contact',
                     'privacy', 'terms', 'accessibility']:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(f'website:{name}')).status_code, 200)

    def test_home_detail_and_missing_home(self):
        home = Property.objects.get(slug='124-oakwood-lane')
        res = self.client.get(home.get_absolute_url())
        self.assertContains(res, '124 Oakwood Lane')
        self.assertContains(res, '$55,000')  # savings vs nearby
        self.assertEqual(self.client.get(reverse('website:home_detail', args=['nope'])).status_code, 404)

    def test_unpublished_home_is_hidden(self):
        Property.objects.filter(slug='42-willow-court').update(is_published=False)
        self.assertNotContains(self.client.get(reverse('website:homes')), '42 Willow Court')
        self.assertEqual(self.client.get(reverse('website:home_detail', args=['42-willow-court'])).status_code, 404)

    def test_filters(self):
        url = reverse('website:homes')
        self.assertEqual(len(self.client.get(url, {'beds': '5'}).context['homes']), 1)
        self.assertEqual(len(self.client.get(url, {'price': '300000'}).context['homes']), 1)
        self.assertEqual(len(self.client.get(url, {'location': 'Austin, TX'}).context['homes']), 2)
        self.assertEqual(len(self.client.get(url, {'status': 'sold'}).context['homes']), 1)
        self.assertEqual(len(self.client.get(url, {'price': 'abc', 'status': 'bogus'}).context['homes']), 6)

    def test_deal_math(self):
        deal = Deal.objects.get(name='Oak Hollow Estate Sale')
        self.assertEqual(deal.total_investment, 320000)
        self.assertEqual(deal.gross_profit, 40000)
        self.assertEqual(deal.buyer_savings, 50000)

    def test_nav_marks_current_page(self):
        res = self.client.get(reverse('website:past_deals'))
        self.assertContains(res, f'href="{reverse("website:past_deals")}" aria-current="page"')

    def test_sitemap_and_robots(self):
        self.assertContains(self.client.get('/sitemap.xml'), '/homes/124-oakwood-lane/')
        self.assertContains(self.client.get('/robots.txt'), 'Sitemap:')


class ContactTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)

    def post(self, **extra):
        data = {'name': 'Pat Buyer', 'email': 'pat@example.com', 'phone': '', 'home': '', 'message': 'Hello', **extra}
        return self.client.post(reverse('website:contact'), data, follow=True)

    def test_prefill_from_home(self):
        res = self.client.get(reverse('website:contact'), {'home': '124-oakwood-lane'})
        self.assertContains(res, '124 Oakwood Lane, Austin, TX')

    def test_valid_message_is_saved(self):
        res = self.post()
        self.assertContains(res, 'Your message was sent')
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_consent_records_wording_and_needs_phone(self):
        res = self.post(sms_consent='on')
        self.assertContains(res, 'Add a phone number')
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.post(sms_consent='on', phone='555-555-5555')
        msg = ContactMessage.objects.get()
        self.assertTrue(msg.sms_consent)
        self.assertIn('Reply STOP', msg.sms_consent_text)

    def test_honeypot_is_ignored(self):
        res = self.post(website='http://spam.example')
        self.assertContains(res, 'Your message was sent')
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_invalid_email_shows_error(self):
        res = self.post(email='not-an-email')
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertContains(res, 'field-error')


class WidgetTests(TestCase):
    def test_chat_message_saved(self):
        res = self.client.post(reverse('website:chat'), {'name': 'Pat', 'email': 'pat@example.com', 'message': 'Hi'})
        self.assertEqual(res.json(), {'ok': True})
        self.assertEqual(ContactMessage.objects.get().home, 'Chat bubble')

    def test_chat_rejects_bad_input_and_spam(self):
        self.assertEqual(self.client.post(reverse('website:chat'), {'name': '', 'email': 'x', 'message': ''}).status_code, 400)
        self.client.post(reverse('website:chat'), {'name': 'B', 'email': 'b@example.com', 'message': 'Hi', 'website': 'spam'})
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertEqual(self.client.get(reverse('website:chat')).status_code, 405)

    def test_footer_widgets_render(self):
        res = self.client.get(reverse('website:home'))
        self.assertContains(res, 'Reviews on Trustpilot')
        self.assertContains(res, 'class="chat-launcher"')
        self.assertContains(res, 'class="to-top"')
        self.assertNotContains(res, 'widget.trustpilot.com')


class TrustTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)

    def test_verify_page_shows_policies_but_no_unfilled_details(self):
        res = self.client.get(reverse('website:verify'))
        self.assertContains(res, 'never ask you to wire money')
        self.assertContains(res, 'Bexar Appraisal District')
        self.assertNotContains(res, 'Registered business')
        self.assertNotContains(res, 'From real buyers and sellers')

    def test_filled_details_and_approved_reviews_appear(self):
        TrustProfile.objects.create(legal_name='Example Homes LLC', filing_number='0801234567')
        Review.objects.create(name='Sam R.', text='Smooth closing.', date='2026-09-01', is_approved=True)
        Review.objects.create(name='Hidden H.', text='Not approved.', date='2026-09-02', is_approved=False)
        res = self.client.get(reverse('website:verify'))
        self.assertContains(res, 'Example Homes LLC')
        self.assertContains(res, '0801234567')
        self.assertContains(res, 'Smooth closing.')
        self.assertNotContains(res, 'Not approved.')

    def test_listing_shows_comps_and_proof(self):
        home = Property.objects.get(slug='124-oakwood-lane')
        res = self.client.get(home.get_absolute_url())
        self.assertContains(res, 'Recent comparable sales nearby')
        self.assertContains(res, 'Travis Central Appraisal District')
        self.assertContains(res, 'Never wire money to me')


class MapTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)

    def test_map_page_lists_pins(self):
        res = self.client.get(reverse('website:map'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['pins']), 6)
        self.assertContains(res, 'id="map-pins"')
        self.assertContains(res, '124 Oakwood Lane')

    def test_map_skips_unpublished_and_unpinned(self):
        Property.objects.filter(slug='42-willow-court').update(is_published=False)
        Property.objects.filter(slug='17-meadow-way').update(latitude=None, longitude=None)
        slugs = [p['slug'] for p in self.client.get(reverse('website:map')).context['pins']]
        self.assertNotIn('42-willow-court', slugs)
        self.assertNotIn('17-meadow-way', slugs)


class OfferTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)

    def post(self, home, **extra):
        data = {'name': 'Pat Buyer', 'email': 'pat@example.com', 'phone': '5125550123', 'offer_price': '',
                'financing': 'cash', 'timeline': '30', 'acknowledged': 'on'}
        data['offer_price'] = f'{home.price:,}'
        data.update(extra)
        return self.client.post(reverse('website:make_offer', args=[home.slug]), data)

    def test_offer_request_saved_with_snapshot(self):
        from .models import OfferRequest
        home = Property.objects.exclude(status='sold').first()
        res = self.post(home)
        self.assertContains(res, 'Your offer request for')
        offer = OfferRequest.objects.get()
        self.assertEqual(offer.offer_price, home.price)
        self.assertEqual(offer.listed_price, home.price)
        self.assertIn('not a contract', offer.acknowledgement_text)

    def test_offer_requires_acknowledgement_and_sane_price(self):
        from .models import OfferRequest
        home = Property.objects.exclude(status='sold').first()
        res = self.post(home, acknowledged='', offer_price='1,000')
        self.assertContains(res, 'not a contract')
        self.assertContains(res, 'below half the asking price')
        self.assertFalse(OfferRequest.objects.exists())

    def test_agent_name_needed_when_working_with_agent(self):
        home = Property.objects.exclude(status='sold').first()
        res = self.post(home, has_agent='on')
        self.assertContains(res, 'name and brokerage')

    def test_no_offers_on_sold_homes(self):
        home = Property.objects.filter(status='sold').first()
        if home:
            self.assertEqual(self.client.get(reverse('website:make_offer', args=[home.slug])).status_code, 404)



class AdminAuthTests(TestCase):
    def signup_data(self, **extra):
        data = {'first_name': 'Ana', 'last_name': 'Lopez', 'email': 'ana@example.com', 'username': 'ana',
                'password1': 'Str0ng-pass-phrase', 'password2': 'Str0ng-pass-phrase', 'website': ''}
        data.update(extra)
        return data

    def test_login_page_uses_custom_design(self):
        r = self.client.get('/admin/login/')
        self.assertContains(r, 'Sign in to your dashboard')
        self.assertContains(r, '/admin/signup/')

    def test_signup_creates_inactive_non_staff_user(self):
        r = self.client.post('/admin/signup/', self.signup_data())
        self.assertContains(r, 'Request sent')
        user = User.objects.get(username='ana')
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(self.client.login(username='ana', password='Str0ng-pass-phrase'))

    def test_signup_rejects_duplicate_email_and_spam(self):
        User.objects.create_user('old', 'ana@example.com', 'x')
        r = self.client.post('/admin/signup/', self.signup_data())
        self.assertContains(r, 'already exists')
        self.client.post('/admin/signup/', self.signup_data(email='new@example.com', website='spam'))
        self.assertFalse(User.objects.filter(username='ana').exists())

    def test_staff_can_still_sign_in(self):
        User.objects.create_user('boss', 'b@example.com', 'pw-12345-abc', is_staff=True)
        r = self.client.post('/admin/login/', {'username': 'boss', 'password': 'pw-12345-abc', 'next': '/admin/'})
        self.assertRedirects(r, '/admin/')

    def test_staff_can_sign_in_with_email(self):
        User.objects.create_user('boss', 'boss@gmail.com', 'pw-12345-abc', is_staff=True)
        r = self.client.post('/admin/login/', {'username': 'boss@gmail.com', 'password': 'pw-12345-abc', 'next': '/admin/'})
        self.assertRedirects(r, '/admin/')

    def test_placeholders_and_disabled_google_button(self):
        r = self.client.get('/admin/signup/')
        self.assertContains(r, 'placeholder="jane.smith@gmail.com"')
        self.assertContains(r, 'Sign up with Google')
        self.assertContains(self.client.get('/admin/login/'), 'disabled title="Google sign-in is not set up yet"')

    @override_settings(GOOGLE_CLIENT_ID='test-id', SOCIALACCOUNT_PROVIDERS={
        'google': {'APPS': [{'client_id': 'test-id', 'secret': 'test-secret'}]}})
    def test_google_button_posts_to_google_login(self):
        r = self.client.get('/admin/login/')
        self.assertContains(r, 'action="/accounts/google/login/"')
        r = self.client.post('/accounts/google/login/')
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r['Location'].startswith('https://accounts.google.com/'))

    def test_new_google_user_waits_for_approval(self):
        from allauth.socialaccount.models import SocialAccount, SocialLogin
        from .adapters import SocialAccountAdapter
        request = RequestFactory().get('/')
        request.session = self.client.session
        login = SocialLogin(user=User(email='new@gmail.com', first_name='New'),
                            account=SocialAccount(provider='google', uid='123'))
        user = SocialAccountAdapter(request).save_user(request, login)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)

    def test_allauth_pages_redirect_to_custom_ones(self):
        self.assertRedirects(self.client.get('/accounts/signup/'), '/admin/signup/')
        self.assertRedirects(self.client.get('/accounts/login/'), '/admin/login/')
