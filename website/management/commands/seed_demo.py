"""Load sample homes, deals, and deals in progress.

    python manage.py seed_demo          # add or update the sample content
    python manage.py seed_demo --clear  # remove all homes and deals first

Safe to run more than once. Replace the samples with your real listings in the admin.
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from website.models import Comparable, Deal, DealInProgress, Property, PropertyPhoto

# Approximate sample map pins in each city. Replace with each real home's exact coordinates.
SAMPLE_PINS = {
    '124-oakwood-lane': dict(latitude=30.3274, longitude=-97.7695),
    '58-hillside-drive': dict(latitude=29.5352, longitude=-98.4847),
    '215-cedar-ridge': dict(latitude=29.7843, longitude=-95.5401),
    '42-willow-court': dict(latitude=32.7254, longitude=-97.4108),
    '9-stone-creek-way': dict(latitude=30.2105, longitude=-97.8392),
    '17-meadow-way': dict(latitude=29.4911, longitude=-98.6110),
}

PROPERTIES = [
    dict(slug='124-oakwood-lane', address='124 Oakwood Lane', city='Austin', price=365000, nearby_price=420000,
         beds=4, baths=3, sqft=2450, year_built=2006, status='for_sale', source='Estate sale',
         summary='Modern four-bedroom on a wooded lot, priced well under the neighborhood.',
         description='The family needed a quick, simple estate sale, so I bought it below market and passed most of that discount on. Open living area, big kitchen, and a private backyard. Fresh paint and a deep clean; nothing else needed.',
         features='Open-concept living and dining\nPrimary suite with walk-in closet\nQuartz kitchen counters\nMature trees and a private yard',
         photos=['photo-1600047509807-ba8f99d2cdde', 'photo-1600210492486-724fe5c67fb0', 'photo-1556911220-bff31c812dba']),
    dict(slug='58-hillside-drive', address='58 Hillside Drive', city='San Antonio', price=329000, nearby_price=389000,
         beds=4, baths=2.5, sqft=2300, year_built=2011, status='for_sale', source='Job relocation',
         summary='Roomy family home in a top-rated school zone.',
         description='The owners relocated for work and needed to close in two weeks. A fast cash purchase let me buy it under market, and the price reflects that.',
         features='Wraparound porch\nTwo living areas\nUpdated bathrooms\nTwo-car garage',
         photos=['photo-1570129477492-45c003edd2be', 'photo-1565183928294-7063f23ce0f8', 'photo-1584622650111-993a426fbf0a']),
    dict(slug='215-cedar-ridge', address='215 Cedar Ridge', city='Houston', price=412000, nearby_price=475000,
         beds=5, baths=3.5, sqft=3100, year_built=2009, status='under_contract', source='Divorce sale',
         summary='Five bedrooms and a stone fireplace for less than the four-beds nearby.',
         description='A big, solid home that needed a quick, clean sale. Currently under contract; backup offers welcome.',
         features='Stone fireplace\nGame room upstairs\nCovered patio\nThree-car garage',
         photos=['photo-1583608205776-bfd35f0d9f83', 'photo-1605774337664-7a846e9cdf17', 'photo-1562438668-bcf0ca6578f0']),
    dict(slug='42-willow-court', address='42 Willow Court', city='Fort Worth', price=298000, nearby_price=345000,
         beds=3, baths=2, sqft=1900, year_built=1999, status='for_sale', source='Sat on the market 7 months',
         summary='Classic brick home in an established neighborhood, under $300K.',
         description='This one was overpriced for months and the seller was ready to move on. I bought it at a fair discount and priced it where it should have been all along, minus a little more.',
         features='All-brick exterior\nUpdated kitchen appliances\nLarge shaded backyard\nQuiet cul-de-sac',
         photos=['photo-1598228723793-52759bba239c', 'photo-1484154218962-a197022b5858', 'photo-1620626011761-996317b8d101']),
    dict(slug='9-stone-creek-way', address='9 Stone Creek Way', city='Austin', price=489000, nearby_price=565000,
         beds=4, baths=3.5, sqft=3300, year_built=2016, status='coming_soon', source='Off-market deal',
         summary='Newer contemporary home that would normally list well over $550K.',
         description='An off-market purchase from an owner who wanted privacy and speed. Listing soon. Contact me to get first look.',
         features='Built in 2016\nFloor-to-ceiling windows\nPool and outdoor kitchen\nHome office',
         photos=['photo-1600596542815-ffad4c1539a9', 'photo-1600121848594-d8644e57abab', 'photo-1750420556288-d0e32a6f517b']),
    dict(slug='17-meadow-way', address='17 Meadow Way', city='San Antonio', price=344000, nearby_price=399000,
         beds=4, baths=3, sqft=2400, year_built=2004, status='sold', source='Foreclosure',
         summary='Bought at a foreclosure auction. Sold to a first-time buyer in 9 days.',
         description='Kept for reference so you can see the kind of savings I aim for on every home.',
         features='Vaulted ceilings\nCovered front porch\nUpdated primary bath\nCorner lot',
         photos=['photo-1568605114967-8130f3a36994', 'photo-1600488999585-e4364713b90a', 'photo-1600210492486-724fe5c67fb0']),
]

DEALS = [
    dict(name='Oak Hollow Estate Sale', location='San Antonio, TX', source='Estate sale', unsplash_id='photo-1572120360610-d971b9d7767c',
         nearby_price=410000, purchase_price=300000, costs=20000, sale_price=360000,
         bought=date(2026, 1, 9), listed=date(2026, 2, 6), sold=date(2026, 3, 12),
         description='Three siblings inherited the home and lived out of state. I closed in 14 days and handled the cleanout. The next owners paid $50,000 less than similar homes on the street.'),
    dict(name='Lakeview Relocation', location='Austin, TX', source='Job relocation', unsplash_id='photo-1605146769289-440113cc3d00',
         nearby_price=525000, purchase_price=390000, costs=25000, sale_price=465000,
         bought=date(2025, 10, 3), listed=date(2025, 11, 7), sold=date(2025, 12, 19),
         description='The sellers had already started new jobs out of state and were paying two mortgages. A fast cash close saved them months. New paint and carpet, then listed well under the neighborhood.'),
    dict(name='Brookside Price Cut', location='Fort Worth, TX', source='Sat on the market', unsplash_id='photo-1628624747186-a941c476b7ef',
         nearby_price=345000, purchase_price=245000, costs=18000, sale_price=305000,
         bought=date(2025, 6, 6), listed=date(2025, 7, 11), sold=date(2025, 8, 8),
         description='Listed for almost a year at an unrealistic price. I bought it at a fair number, fixed a leaky roof, and sold it to a young family in under three weeks.'),
]

IN_PROGRESS = [
    dict(name='Pecan Grove Two-Story', location='Houston, TX', unsplash_id='photo-1592595896616-c37162298647', stage='inspection', progress=30,
         expected_listing='December 2026', update='Inspection came back clean apart from an older water heater. Closing is set for next month.'),
    dict(name='Rolling Hills Contemporary', location='Austin, TX', unsplash_id='photo-1613490493576-7fde63acd811', stage='refresh', progress=70,
         expected_listing='November 2026', update='Fresh paint and new carpet upstairs this week. Listing photos are next.'),
    dict(name='Magnolia Corner', location='Fort Worth, TX', unsplash_id='photo-1580587771525-78b9dba3b914', stage='offer', progress=10,
         expected_listing='February 2027', update='The seller is moving overseas and needed a fast close. Under contract at a solid discount.'),
]


class Command(BaseCommand):
    help = 'Load sample homes, past deals, and deals in progress.'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Delete all homes, deals, and deals in progress first.')

    @transaction.atomic
    def handle(self, *args, clear=False, **options):
        if clear:
            Property.objects.all().delete()
            Deal.objects.all().delete()
            DealInProgress.objects.all().delete()

        for order, data in enumerate(PROPERTIES):
            data = dict(data)
            data.update(SAMPLE_PINS.get(data['slug'], {}))
            photos = data.pop('photos')
            home, _ = Property.objects.update_or_create(slug=data['slug'], defaults={**data, 'order': order})
            if not home.comparables.exists():
                # Three sample nearby sales that average out to the listing's nearby price.
                street = home.address.split(' ', 1)[1]
                for i, (delta, months) in enumerate([(-12000, 2), (4000, 4), (8000, 5)]):
                    Comparable.objects.create(
                        property=home, address=f'{int(home.address.split()[0]) + 6 + i * 14} {street}',
                        sold_date=date(2026, 9 - months, 15), sold_price=home.nearby_price + delta,
                        beds=home.beds, baths=home.baths, sqft=home.sqft + (i - 1) * 120, source='Sample data')
            if not home.photos.exists():
                for i, pid in enumerate(photos):
                    alt = f'Front of {home.address}' if i == 0 else f'Inside {home.address}'
                    PropertyPhoto.objects.create(property=home, unsplash_id=pid, alt=alt, order=i)

        for order, data in enumerate(DEALS):
            Deal.objects.update_or_create(name=data['name'], defaults={**data, 'order': order})
        for order, data in enumerate(IN_PROGRESS):
            DealInProgress.objects.update_or_create(name=data['name'], defaults={**data, 'order': order})

        self.stdout.write(self.style.SUCCESS(
            f'Loaded {len(PROPERTIES)} homes, {len(DEALS)} past deals, and {len(IN_PROGRESS)} deals in progress.'))
