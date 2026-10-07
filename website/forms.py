from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ContactMessage, OfferRequest

SMS_CONSENT_TEXT = (
    'I agree that Thistledown Homes may call and text me at the number above about my inquiry, '
    'including with automated technology. Consent is not required to buy a home. Message frequency varies. '
    'Message and data rates may apply. Reply STOP to opt out or HELP for help.'
)


class ContactForm(forms.ModelForm):
    # Honeypot: real visitors never see or fill this field.
    website = forms.CharField(required=False, label='Leave this empty',
                              widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}))

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'home', 'message', 'sms_consent']
        labels = {
            'home': 'Home you are asking about',
            'sms_consent': SMS_CONSENT_TEXT,
        }
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'name'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'phone': forms.TextInput(attrs={'type': 'tel', 'autocomplete': 'tel'}),
            'message': forms.Textarea(attrs={'rows': 5}),
        }

    def clean_sms_consent(self):
        consent = self.cleaned_data.get('sms_consent')
        if consent and not self.data.get('phone', '').strip():
            raise forms.ValidationError('Add a phone number if you would like calls or texts.')
        return consent

    def is_spam(self):
        return bool(self.cleaned_data.get('website'))

    def save(self, commit=True):
        msg = super().save(commit=False)
        # Keep a provable record of the exact wording the person agreed to.
        msg.sms_consent_text = SMS_CONSENT_TEXT if msg.sms_consent else ''
        if commit:
            msg.save()
        return msg


class ChatForm(forms.ModelForm):
    """Quick message from the chat bubble. Saved as a ContactMessage."""
    website = forms.CharField(required=False)

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']

    def is_spam(self):
        return bool(self.cleaned_data.get('website'))

    def save(self, commit=True):
        msg = super().save(commit=False)
        msg.home = 'Chat bubble'
        if commit:
            msg.save()
        return msg


OFFER_ACK_TEXT = (
    'I understand this is a request to start an offer, not a contract. Nothing is binding until both '
    'sides sign a written purchase contract, and any earnest money is paid only to a licensed title '
    'company, never to Thistledown Homes directly.'
)


class OfferForm(forms.ModelForm):
    """Start-an-offer request for one home. Saved as an OfferRequest."""
    website = forms.CharField(required=False, label='Leave this empty',
                              widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}))
    offer_price = forms.CharField(label='Your offer', widget=forms.TextInput(attrs={
        'inputmode': 'numeric', 'autocomplete': 'off', 'placeholder': '450,000', 'data-money': ''}))
    acknowledged = forms.BooleanField(label=OFFER_ACK_TEXT, error_messages={
        'required': 'Please confirm you understand this is not a contract.'})

    class Meta:
        model = OfferRequest
        fields = ['name', 'email', 'phone', 'offer_price', 'financing', 'lender', 'timeline',
                  'wants_showing', 'has_agent', 'agent_name', 'notes', 'acknowledged', 'sms_consent']
        labels = {
            'phone': 'Phone',
            'financing': 'How are you paying?',
            'lender': 'Lender',
            'timeline': 'When would you like to close?',
            'wants_showing': 'I would like to see the home before finalizing',
            'has_agent': 'I am working with a real estate agent',
            'agent_name': 'Agent name and brokerage',
            'notes': 'Anything else?',
            'sms_consent': SMS_CONSENT_TEXT,
        }
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'name', 'placeholder': 'John Smith'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'johnsmith@gmail.com'}),
            'phone': forms.TextInput(attrs={'type': 'tel', 'autocomplete': 'tel', 'placeholder': '(512) 555-0123'}),
            'lender': forms.TextInput(attrs={'placeholder': 'e.g. Chase, local credit union'}),
            'agent_name': forms.TextInput(attrs={'placeholder': 'Jane Doe, ABC Realty'}),
            'notes': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Questions, requests, or anything about your offer.'}),
        }

    def __init__(self, *args, home=None, **kwargs):
        self.home = home
        super().__init__(*args, **kwargs)
        self.fields['financing'].choices = [('', 'Choose one')] + list(OfferRequest.Financing.choices)
        self.fields['timeline'].choices = [('', 'Choose one')] + list(OfferRequest.Timeline.choices)

    def clean_offer_price(self):
        raw = ''.join(c for c in self.cleaned_data['offer_price'] if c.isdigit())
        if not raw:
            raise forms.ValidationError('Enter your offer in dollars, for example 450,000.')
        value = int(raw)
        if self.home and value < self.home.price * 0.5:
            raise forms.ValidationError('Offers below half the asking price cannot be considered.')
        if value > 50_000_000:
            raise forms.ValidationError('Please check this amount.')
        return value

    def clean(self):
        data = super().clean()
        if data.get('has_agent') and not data.get('agent_name', '').strip():
            self.add_error('agent_name', "Add your agent's name and brokerage.")
        return data

    def is_spam(self):
        return bool(self.cleaned_data.get('website'))

    def save(self, commit=True):
        offer = super().save(commit=False)
        offer.home = self.home
        offer.home_label = f'{self.home.address}, {self.home.location}'
        offer.listed_price = self.home.price
        offer.acknowledgement_text = OFFER_ACK_TEXT
        offer.sms_consent_text = SMS_CONSENT_TEXT if offer.sms_consent else ''
        if commit:
            offer.save()
        return offer


class AdminSignupForm(UserCreationForm):
    """Request access to the admin. New accounts stay inactive until the owner approves them."""
    website = forms.CharField(required=False, label='Leave this empty',
                              widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'email', 'username')
        widgets = {
            'first_name': forms.TextInput(attrs={'autocomplete': 'given-name', 'placeholder': 'Jane'}),
            'last_name': forms.TextInput(attrs={'autocomplete': 'family-name', 'placeholder': 'Smith'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'jane.smith@gmail.com'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('first_name', 'last_name', 'email'):
            self.fields[name].required = True
        self.fields['username'].widget.attrs['placeholder'] = 'janesmith'
        self.fields['password1'].widget.attrs['placeholder'] = 'At least 8 characters'
        self.fields['password2'].widget.attrs['placeholder'] = 'Re-enter your password'

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def is_spam(self):
        return bool(self.cleaned_data.get('website'))

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        user.is_staff = False
        if commit:
            user.save()
        return user
