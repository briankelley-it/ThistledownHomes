from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.core.mail import send_mail


def notify_access_request(user, via='the sign-up form'):
    """Email the owner that someone asked for dashboard access."""
    if settings.CONTACT_NOTIFY_EMAIL:
        send_mail(
            f'New admin access request from {user.get_full_name() or user.email}',
            f'{user.get_full_name()} <{user.email}> asked for admin access as "{user.username}" via {via}.\n\n'
            'To approve, open Users in the admin, tick Active and Staff status, and choose their permissions.',
            settings.DEFAULT_FROM_EMAIL, [settings.CONTACT_NOTIFY_EMAIL], fail_silently=True)


class AccountAdapter(DefaultAccountAdapter):
    # Password sign-ups go through /admin/signup/, not allauth's own pages.
    def is_open_for_signup(self, request):
        return False


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True

    def save_user(self, request, sociallogin, form=None):
        # New Google accounts wait for the owner's approval, like password sign-ups.
        user = sociallogin.user
        user.is_active = False
        user.is_staff = False
        user = super().save_user(request, sociallogin, form)
        notify_access_request(user, via='Google')
        return user
