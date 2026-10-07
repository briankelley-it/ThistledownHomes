from django.db import models
from django.urls import reverse


class PhotoMixin(models.Model):
    """A photo can be an uploaded file or, until you have real photos, an Unsplash photo ID."""
    image = models.ImageField(upload_to='photos/', blank=True, help_text='Upload a real photo. This is used when set.')
    unsplash_id = models.CharField(
        max_length=80, blank=True,
        help_text="Placeholder photo, e.g. photo-1568605114967-8130f3a36994. Used only when no image is uploaded.")

    class Meta:
        abstract = True

    def photo_url(self, width=900, height=None):
        if self.image:
            return self.image.url
        if self.unsplash_id:
            size = f'&h={height}' if height else ''
            return f'https://images.unsplash.com/{self.unsplash_id}?auto=format&fit=crop&w={width}{size}&q=78'
        return ''

    # Sizes used by the templates.
    def card_url(self):
        return self.photo_url(800, 560)

    def large_url(self):
        return self.photo_url(1400, 900)

    def thumb_url(self):
        return self.photo_url(240, 160)

    def wide_url(self):
        return self.photo_url(1100, 760)


class Property(models.Model):
    class Status(models.TextChoices):
        FOR_SALE = 'for_sale', 'For Sale'
        UNDER_CONTRACT = 'under_contract', 'Under Contract'
        COMING_SOON = 'coming_soon', 'Coming Soon'
        SOLD = 'sold', 'Sold'

    slug = models.SlugField(unique=True, help_text='Used in the web address, e.g. 124-oakwood-lane')
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2, default='TX')
    price = models.PositiveIntegerField(help_text='Asking price in dollars')
    nearby_price = models.PositiveIntegerField(
        help_text='What similar homes nearby recently sold for. Use real comparable sales.')
    beds = models.PositiveSmallIntegerField()
    baths = models.DecimalField(max_digits=3, decimal_places=1)
    sqft = models.PositiveIntegerField('Square feet')
    year_built = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.FOR_SALE)
    source = models.CharField('Why it is priced lower', max_length=120, help_text='e.g. Estate sale, Job relocation')
    summary = models.CharField(max_length=200, help_text='One line shown on the listing card')
    description = models.TextField()
    features = models.TextField(blank=True, help_text='One highlight per line')
    county_record_url = models.URLField(
        'County ownership record', blank=True,
        help_text='Link to this property on the county appraisal district site, showing your company as owner.')
    portal_url = models.URLField(
        'Zillow / Realtor.com listing', blank=True,
        help_text='Link to the same home on a major listing site, once it is on the MLS.')
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text='Map pin. In Google Maps, right-click the house and click the coordinates to copy them, e.g. 30.267153')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text='e.g. -97.743057')
    is_published = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0, help_text='Lower numbers show first')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created']
        verbose_name_plural = 'properties'

    def __str__(self):
        return f'{self.address}, {self.city}'

    def get_absolute_url(self):
        return reverse('website:home_detail', args=[self.slug])

    @property
    def location(self):
        return f'{self.city}, {self.state}'

    @property
    def savings(self):
        return max(self.nearby_price - self.price, 0)

    @property
    def feature_list(self):
        return [line.strip() for line in self.features.splitlines() if line.strip()]

    @property
    def cover(self):
        return self.photos.first()

    @property
    def appraisal_district(self):
        """Public county site where anyone can confirm who owns the property."""
        return APPRAISAL_DISTRICTS.get(self.city)


# County appraisal districts where buyers can look up ownership records for free.
APPRAISAL_DISTRICTS = {
    'Austin': ('Travis Central Appraisal District', 'https://traviscad.org'),
    'San Antonio': ('Bexar Appraisal District', 'https://www.bcad.org'),
    'Fort Worth': ('Tarrant Appraisal District', 'https://www.tad.org'),
    'Houston': ('Harris Central Appraisal District', 'https://hcad.org'),
}


class Comparable(models.Model):
    """A recent nearby sale that supports a listing's "similar homes nearby" price."""
    property = models.ForeignKey(Property, related_name='comparables', on_delete=models.CASCADE)
    address = models.CharField(max_length=200)
    sold_date = models.DateField()
    sold_price = models.PositiveIntegerField()
    beds = models.PositiveSmallIntegerField(null=True, blank=True)
    baths = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    sqft = models.PositiveIntegerField(null=True, blank=True)
    source = models.CharField(max_length=60, default='MLS', help_text='Where the sale is recorded, e.g. MLS or County records')

    class Meta:
        ordering = ['-sold_date']

    def __str__(self):
        return f'{self.address} (${self.sold_price:,})'


class PropertyPhoto(PhotoMixin):
    property = models.ForeignKey(Property, related_name='photos', on_delete=models.CASCADE)
    alt = models.CharField('Description', max_length=200, blank=True, help_text='Describe the photo for screen readers')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.alt or f'Photo of {self.property}'


class Deal(PhotoMixin):
    """A completed purchase and sale. Also powers the Investment Numbers section."""
    name = models.CharField(max_length=120)
    location = models.CharField(max_length=120, help_text='e.g. San Antonio, TX')
    source = models.CharField('Where the discount came from', max_length=120)
    nearby_price = models.PositiveIntegerField(help_text='What similar homes nearby sold for')
    purchase_price = models.PositiveIntegerField()
    costs = models.PositiveIntegerField(help_text='Refresh, closing, and holding costs')
    sale_price = models.PositiveIntegerField()
    bought = models.DateField()
    listed = models.DateField()
    sold = models.DateField()
    description = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', '-sold']

    def __str__(self):
        return self.name

    @property
    def total_investment(self):
        return self.purchase_price + self.costs

    @property
    def gross_profit(self):
        return self.sale_price - self.total_investment

    @property
    def buyer_savings(self):
        return max(self.nearby_price - self.sale_price, 0)

    @property
    def months(self):
        days = (self.sold - self.bought).days
        return round(days / 30.4, 1)

    def share(self, amount):
        """Percent of the nearby price, for the breakdown bar."""
        return round(max(amount, 0) / self.nearby_price * 100, 1) if self.nearby_price else 0

    @property
    def bars(self):
        return {
            'purchase': self.share(self.purchase_price),
            'costs': self.share(self.costs),
            'profit': self.share(self.gross_profit),
            'saved': self.share(self.buyer_savings),
        }


class DealInProgress(PhotoMixin):
    class Stage(models.TextChoices):
        OFFER = 'offer', 'Offer accepted'
        INSPECTION = 'inspection', 'Inspection'
        CLOSING = 'closing', 'Closing'
        REFRESH = 'refresh', 'Light refresh'
        PHOTOS = 'photos', 'Listing photos'
        LISTED = 'listed', 'Listed'

    name = models.CharField(max_length=120)
    location = models.CharField(max_length=120)
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.OFFER)
    progress = models.PositiveSmallIntegerField(default=10, help_text='0 to 100')
    expected_listing = models.CharField(max_length=60, help_text='e.g. December 2026')
    update = models.TextField('Latest update')
    is_published = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-updated']
        verbose_name = 'deal in progress'
        verbose_name_plural = 'deals in progress'

    def __str__(self):
        return self.name

    @property
    def stage_steps(self):
        values = list(self.Stage.values)
        current = values.index(self.stage)
        return [{'label': label, 'state': 'done' if i < current else 'current' if i == current else ''}
                for i, label in enumerate(self.Stage.labels)]


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150)
    phone = models.CharField(max_length=30, blank=True)
    home = models.CharField('Home asked about', max_length=200, blank=True)
    message = models.TextField(max_length=3000)
    sms_consent = models.BooleanField('Agreed to calls and texts', default=False)
    sms_consent_text = models.TextField(blank=True, help_text='Exact consent wording shown when they agreed')
    created = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'{self.name} ({self.created:%b %d, %Y})'


class TrustProfile(models.Model):
    """Business details shown on the Verify page. Only filled-in fields are displayed."""
    legal_name = models.CharField(max_length=150, blank=True, help_text='e.g. Thistledown Homes LLC')
    entity_type = models.CharField(max_length=60, blank=True, help_text='e.g. Texas limited liability company')
    filing_number = models.CharField('Texas SOS file number', max_length=40, blank=True)
    formed_year = models.PositiveSmallIntegerField(null=True, blank=True)
    business_address = models.CharField(max_length=200, blank=True)
    license_note = models.CharField(
        max_length=200, blank=True,
        help_text='e.g. "Not a licensed real estate agent" or your TREC license number if you get one')
    title_companies = models.TextField(blank=True, help_text='Title companies you close with, one per line')
    google_business_url = models.URLField('Google Business Profile', blank=True)
    bbb_url = models.URLField('Better Business Bureau profile', blank=True)
    linkedin_url = models.URLField('LinkedIn', blank=True)
    facebook_url = models.URLField('Facebook', blank=True)
    instagram_url = models.URLField('Instagram', blank=True)

    class Meta:
        verbose_name = 'trust profile'
        verbose_name_plural = 'trust profile'

    def __str__(self):
        return 'Business details (Verify page)'

    @classmethod
    def load(cls):
        return cls.objects.first() or cls()

    @property
    def title_company_list(self):
        return [line.strip() for line in self.title_companies.splitlines() if line.strip()]

    @property
    def profiles(self):
        return [(label, url) for label, url in [
            ('Google Business Profile', self.google_business_url), ('Better Business Bureau', self.bbb_url),
            ('LinkedIn', self.linkedin_url), ('Facebook', self.facebook_url), ('Instagram', self.instagram_url),
        ] if url]

    @property
    def has_registration(self):
        return bool(self.legal_name or self.filing_number)


class Review(models.Model):
    """A real review from a real buyer or seller. Only approved reviews appear on the site."""
    class Role(models.TextChoices):
        BUYER = 'buyer', 'Buyer'
        SELLER = 'seller', 'Seller'

    name = models.CharField(max_length=80, help_text='As the reviewer agreed to be shown, e.g. "Maria G."')
    location = models.CharField(max_length=80, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.BUYER)
    rating = models.PositiveSmallIntegerField(default=5, help_text='1 to 5, exactly as the reviewer gave it')
    text = models.TextField()
    date = models.DateField()
    source = models.CharField(max_length=40, default='Google', help_text='Where the review was posted')
    source_url = models.URLField(blank=True, help_text='Link to the original review so visitors can check it')
    is_approved = models.BooleanField(
        default=False, help_text='Show on the site. Only approve genuine reviews; never write or edit them yourself.')

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.name} ({self.rating}/5)'

    @property
    def stars(self):
        return range(self.rating)


class OfferRequest(models.Model):
    """A buyer's non-binding request to start an offer on a home. Not a contract."""

    class Financing(models.TextChoices):
        CASH = 'cash', 'Cash'
        PREAPPROVED = 'preapproved', 'Mortgage, already pre-approved'
        MORTGAGE = 'mortgage', 'Mortgage, not pre-approved yet'
        OTHER = 'other', 'Other or not sure'

    class Timeline(models.TextChoices):
        ASAP = 'asap', 'As soon as possible'
        DAYS_30 = '30', 'Within 30 days'
        DAYS_45 = '45', 'Within 45 days'
        DAYS_60 = '60', 'Within 60 days'
        FLEXIBLE = 'flexible', 'Flexible'

    class Stage(models.TextChoices):
        NEW = 'new', 'New'
        CONTACTED = 'contacted', 'Contacted'
        SHOWING = 'showing', 'Showing scheduled'
        CONTRACT = 'contract', 'Under contract'
        CLOSED = 'closed', 'Closed'
        DECLINED = 'declined', 'Declined or withdrawn'

    home = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, related_name='offer_requests')
    home_label = models.CharField('Home', max_length=200, help_text='Address at the time of the request')
    listed_price = models.PositiveIntegerField(help_text='Asking price at the time of the request')
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150)
    phone = models.CharField(max_length=30)
    offer_price = models.PositiveIntegerField()
    financing = models.CharField(max_length=20, choices=Financing.choices)
    lender = models.CharField('Lender (if any)', max_length=120, blank=True)
    timeline = models.CharField('Closing timeline', max_length=20, choices=Timeline.choices)
    wants_showing = models.BooleanField('Wants a showing first', default=True)
    has_agent = models.BooleanField('Working with an agent', default=False)
    agent_name = models.CharField(max_length=120, blank=True)
    notes = models.TextField(max_length=3000, blank=True)
    acknowledged = models.BooleanField('Acknowledged non-binding terms', default=False)
    acknowledgement_text = models.TextField(blank=True, help_text='Exact wording they agreed to')
    sms_consent = models.BooleanField('Agreed to calls and texts', default=False)
    sms_consent_text = models.TextField(blank=True)
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.NEW)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'{self.name}: ${self.offer_price:,} on {self.home_label}'
