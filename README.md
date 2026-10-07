# Thistledown Homes

**Fictional demo.** Thistledown Homes is a made-up company. This is a sample website, not a real business. No homes are for sale, no offers are real, and every listing, deal, price, and contact detail is invented for illustration.

A Django website for a pretend independent real estate investor who buys higher-value homes below market and resells them at more affordable prices.

## Pages

| URL | Page |
|---|---|
| `/` | Home: intro, short "why", featured homes, latest deal |
| `/homes/` | Homes For Sale with price, bedroom, location, and status filters, plus "Saved only" |
| `/homes/<slug>/` | One page per home, with photos, savings vs nearby, and highlights |
| `/map/` | Map of every home with price pins, status filters, and a synced list |
| `/how-it-works/` | The idea, a price example, and the 4-step process |
| `/past-deals/` | Completed deals plus the Investment Numbers breakdown |
| `/deals-in-progress/` | Homes being bought or prepared to list |
| `/about/` | About the (fictional) investor |
| `/verify/` | Verify page: wire fraud warning, buyer protections, county record lookup, and optional business details and reviews |
| `/contact/` | Contact form (saves messages to the admin) |
| `/privacy/`, `/terms/`, `/accessibility/` | Legal pages |
| `/admin/` | Dashboard to manage everything (custom sign-in page) |
| `/admin/signup/` | Request a dashboard account. New accounts stay off until an admin ticks **Active** and **Staff status** under Users |
| `/sitemap.xml`, `/robots.txt` | Generated automatically. The demo blocks all search engines |

## Run it on your computer

Requires Python 3.12 or newer.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Then open 127.0.0.1:8000 in your browser for the site, and 127.0.0.1:8000/admin for the dashboard.

`seed_demo` loads the sample homes and deals. Run `python manage.py seed_demo --clear` to reset them, or edit and delete them in the admin.

Run the tests with `python manage.py test`.

## Managing content

Log in at `/admin/`:

- **Properties**: add a home, set its price and the **nearby price** (what similar homes sold for), and add photos at the bottom. Upload photos or paste an Unsplash photo ID as a placeholder. Untick **Is published** to hide a home without deleting it.
- **Deals**: completed deals. Profit and buyer savings are calculated automatically and appear on Past Deals and the home page stats.
- **Deals in progress**: pick the stage and progress percent.
- **Contact messages**: every message from the contact form, including the exact call and text consent wording when someone opted in. Tick **Handled** after replying.
- **Map pins**: each property has **Latitude** and **Longitude** under "Map location". Homes without coordinates are left off the map. The map uses MapLibre with free OpenFreeMap styles. To use another provider, set `MAP_STYLE_LIGHT` and `MAP_STYLE_DARK` to any MapLibre style URL.
- **Trust profile**: company name, filing number, business address, title companies, and profile links. Each item appears on the Verify page only once it is filled in.
- **Reviews**: reviews with **Is approved** ticked appear on the site.
- **Comparables**: recent nearby sales shown on each property page. The sample ones are labeled "Sample data".

**Hero background video:** `website/static/website/video/hero-houses.mp4`, with `hero-poster.jpg` shown while it loads. To change it, replace both files and keep the same names. A short, silent clip under about 5 MB works best.

## Google sign-in for the admin

The sign-in and sign-up pages have a Google button. It stays greyed out until it is connected:

1. In Google Cloud Console, create an **OAuth client ID** (type: Web application).
2. Add the authorized redirect URI `/accounts/google/login/callback/` on your domain (and on 127.0.0.1:8000 for local testing).
3. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` and restart the site.

## Project layout

```
thistledown/          Django settings and top-level URLs
website/
  models.py          Property, PropertyPhoto, Deal, DealInProgress, ContactMessage, and more
  views.py           One view per page
  urls.py            Page URLs
  forms.py           Contact form (spam honeypot, call/text consent)
  admin.py           Admin dashboard setup
  templates/website/ Page templates and partials
  static/website/    styles.css, site.js (menu and cookie consent), main.js (favorites, tabs, filters), map.js
  management/commands/seed_demo.py   Sample content
  tests.py           Automated tests
templates/           Not-found page and admin sign-in templates
```

## Settings

Copy `.env.example` and set the values as environment variables. The most important ones are `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, and `DJANGO_CSRF_TRUSTED_ORIGINS`. The site name, email, phone, and area shown on the pages come from `SITE_EMAIL`, `SITE_PHONE`, `SITE_PHONE_LINK`, `SITE_AREA`, and `SITE_DOMAIN`. The defaults are fake placeholder values.

## Deploy

This is a Python app, so it needs a host that runs Django, not a static host.

1. Set the environment variables from `.env.example`.
2. Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
3. Start: `gunicorn thistledown.wsgi`
4. Create a login once: `python manage.py createsuperuser`

Notes:

- The database is SQLite in `db.sqlite3`. Use a host with a persistent disk (or point `DJANGO_DB_PATH` at one) so data survives redeploys.
- Uploaded photos are saved in `media/`. Django does not serve them when `DJANGO_DEBUG=0`, so configure the host to serve `/media/` from that folder.
- Contact messages are always saved in the admin. To also send an email, set `CONTACT_NOTIFY_EMAIL` and the SMTP settings.

## Features

Investor disclosures and footer disclaimer, "nearby price" comparison disclaimers, Equal Housing Opportunity statement, investment numbers disclaimer, cookie consent with Global Privacy Control support, optional call and text consent with the wording stored per message, privacy policy, terms, and accessibility pages, CSRF protection and a spam honeypot on forms, light and dark themes, saved homes, and keyboard support with a skip link.

The legal pages are sample text for a fictional company and are not legal advice.
