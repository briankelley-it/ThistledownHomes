from django.contrib import admin
from django.utils.html import format_html

from .models import (Comparable, ContactMessage, Deal, DealInProgress, OfferRequest, Property, PropertyPhoto,
                     Review, TrustProfile)


def preview(obj, width=120):
    url = obj.photo_url(240, 160) if obj else ''
    return format_html('<img src="{}" style="width:{}px;border-radius:6px">', url, width) if url else '-'


class PropertyPhotoInline(admin.TabularInline):
    model = PropertyPhoto
    extra = 1
    fields = ('thumbnail', 'image', 'unsplash_id', 'alt', 'order')
    readonly_fields = ('thumbnail',)

    @admin.display(description='Preview')
    def thumbnail(self, obj):
        return preview(obj, 90)


class ComparableInline(admin.TabularInline):
    model = Comparable
    extra = 1
    fields = ('address', 'sold_date', 'sold_price', 'beds', 'baths', 'sqft', 'source')


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('address', 'city', 'price', 'nearby_price', 'savings_display', 'status', 'is_published', 'order')
    list_editable = ('status', 'is_published', 'order')
    list_filter = ('status', 'city', 'is_published')
    search_fields = ('address', 'city', 'summary')
    prepopulated_fields = {'slug': ('address',)}
    inlines = [PropertyPhotoInline, ComparableInline]
    fieldsets = (
        (None, {'fields': ('address', 'slug', 'city', 'state', 'status', 'is_published', 'order')}),
        ('Price', {'fields': ('price', 'nearby_price', 'source')}),
        ('Details', {'fields': ('beds', 'baths', 'sqft', 'year_built')}),
        ('Description', {'fields': ('summary', 'description', 'features')}),
        ('Map location', {'fields': ('latitude', 'longitude')}),
        ('Proof for buyers', {'fields': ('county_record_url', 'portal_url'),
                              'description': 'Links that let buyers confirm this listing on their own.'}),
    )

    @admin.display(description='Under nearby')
    def savings_display(self, obj):
        return f'${obj.savings:,}'


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'purchase_price', 'sale_price', 'profit_display', 'buyer_savings_display', 'sold', 'order')
    list_editable = ('order',)
    readonly_fields = ('thumbnail',)
    fieldsets = (
        (None, {'fields': ('name', 'location', 'source', 'order')}),
        ('Photo', {'fields': ('thumbnail', 'image', 'unsplash_id')}),
        ('Numbers', {'fields': ('nearby_price', 'purchase_price', 'costs', 'sale_price')}),
        ('Timeline', {'fields': ('bought', 'listed', 'sold')}),
        ('Story', {'fields': ('description',)}),
    )

    @admin.display(description='Preview')
    def thumbnail(self, obj):
        return preview(obj)

    @admin.display(description='Gross profit')
    def profit_display(self, obj):
        return f'${obj.gross_profit:,}'

    @admin.display(description='Buyer saved')
    def buyer_savings_display(self, obj):
        return f'${obj.buyer_savings:,}'


@admin.register(DealInProgress)
class DealInProgressAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'stage', 'progress', 'expected_listing', 'is_published', 'order')
    list_editable = ('stage', 'progress', 'is_published', 'order')
    readonly_fields = ('thumbnail',)
    fields = ('name', 'location', 'thumbnail', 'image', 'unsplash_id', 'stage', 'progress', 'expected_listing', 'update', 'is_published', 'order')

    @admin.display(description='Preview')
    def thumbnail(self, obj):
        return preview(obj)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'home', 'created', 'sms_consent', 'handled')
    list_editable = ('handled',)
    list_filter = ('handled', 'sms_consent', 'created')
    search_fields = ('name', 'email', 'phone', 'home', 'message')
    readonly_fields = ('name', 'email', 'phone', 'home', 'message', 'sms_consent', 'sms_consent_text', 'created')
    date_hierarchy = 'created'

    def has_add_permission(self, request):
        return False


@admin.register(OfferRequest)
class OfferRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'home_label', 'offer_display', 'asking_display', 'financing', 'timeline', 'stage', 'created')
    list_editable = ('stage',)
    list_filter = ('stage', 'financing', 'timeline', 'created')
    search_fields = ('name', 'email', 'phone', 'home_label', 'notes')
    date_hierarchy = 'created'
    fieldsets = (
        ('Follow-up', {'fields': ('stage',)}),
        ('Home', {'fields': ('home', 'home_label', 'listed_price')}),
        ('Buyer', {'fields': ('name', 'email', 'phone', 'has_agent', 'agent_name')}),
        ('Offer', {'fields': ('offer_price', 'financing', 'lender', 'timeline', 'wants_showing', 'notes')}),
        ('Consent record', {'fields': ('acknowledged', 'acknowledgement_text', 'sms_consent', 'sms_consent_text', 'created')}),
    )
    readonly_fields = ('home', 'home_label', 'listed_price', 'name', 'email', 'phone', 'has_agent', 'agent_name',
                       'offer_price', 'financing', 'lender', 'timeline', 'wants_showing', 'notes', 'acknowledged',
                       'acknowledgement_text', 'sms_consent', 'sms_consent_text', 'created')

    @admin.display(description='Offer', ordering='offer_price')
    def offer_display(self, obj):
        return f'${obj.offer_price:,}'

    @admin.display(description='Asking', ordering='listed_price')
    def asking_display(self, obj):
        return f'${obj.listed_price:,}'

    def has_add_permission(self, request):
        return False


@admin.register(TrustProfile)
class TrustProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Registration', {'fields': ('legal_name', 'entity_type', 'filing_number', 'formed_year', 'business_address', 'license_note'),
                          'description': 'Shown on the Verify page once filled in. Use your real, registered details only.'}),
        ('Closings', {'fields': ('title_companies',)}),
        ('Public profiles', {'fields': ('google_business_url', 'bbb_url', 'linkedin_url', 'facebook_url', 'instagram_url')}),
    )

    def has_add_permission(self, request):
        return not TrustProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'rating', 'source', 'date', 'is_approved')
    list_editable = ('is_approved',)
    list_filter = ('is_approved', 'role', 'source')
