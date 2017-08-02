from __future__ import unicode_literals

from django.utils.encoding import python_2_unicode_compatible
from django.contrib.sitemaps import Sitemap


@python_2_unicode_compatible
class SubdomainSite(object):
    """
    SubdomainSite shares the interface of Site and adds subdomain support.

    The save() and delete() methods raise NotImplementedError.
    """
    def __init__(self, subdomain, site=None):
        self.subdomain = subdomain
        self.extend_site(site)

    def __str__(self):
        return self.domain

    def extend_site(self, site):
        """Always returns the root level site extended with subdomain."""
        if issubclass(site.__class__, self.__class__):
            return self.extend_site(site.root_site)
        elif hasattr(site, 'domain'):
            self.root_site = site
        self.domain = self.name = '{0}.{1}'.format(self.subdomain, site)
        return self

    def save(self, force_insert=False, force_update=False):
        raise NotImplementedError('RequestSite cannot be saved.')

    def delete(self):
        raise NotImplementedError('RequestSite cannot be deleted.')


class SubdomainSitemap(Sitemap):
    """Adds subdomain support to sitemaps"""
    subdomain = None

    def get_urls(self, page=1, site=None, protocol=None):
        """Always uses this sitemap's subdomain if supplied."""
        # Determine protocol
        if self.protocol is not None:
            protocol = self.protocol
        if protocol is None:
            protocol = 'http'

        # Determine domain
        if site is None and self.subdomain is None:
            if django_apps.is_installed('django.contrib.sites'):
                Site = django_apps.get_model('sites.Site')
                try:
                    site = Site.objects.get_current()
                except Site.DoesNotExist:
                    pass
            if site is None:
                raise ImproperlyConfigured(
                    "To use sitemaps, either enable the sites framework or pass "
                    "a Site/RequestSite object in your view."
                )
        else:
            # Setting a subdomain site overrides supplied site
            site = self.subdomain
        domain = site.domain

        if getattr(self, 'i18n', False):
            urls = []
            current_lang_code = translation.get_language()
            for lang_code, lang_name in settings.LANGUAGES:
                translation.activate(lang_code)
                urls += self._urls(page, protocol, domain)
            translation.activate(current_lang_code)
        else:
            urls = self._urls(page, protocol, domain)

        return urls
