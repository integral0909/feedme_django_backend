from django.shortcuts import render
from django.views.generic import TemplateView
from main.models import Recipe


def load_flatpage(request, page='home'):
    context = {'title': page.title()}
    return render(request, 'flatpages/%s.html' % page, context)


class FlatView(TemplateView):
    template_name = None

    def get_context_data(self, **kwargs):
        context = super(FlatView, self).get_context_data(**kwargs)
        context['title'] = self.template_name.split('.')[0].title()
        return context

    def get_template_names(self):
        """
        Returns a list of template names to be used for the request. Must return
        a list. May not be called if render_to_response is overridden.
        """
        if self.template_name is None:
            raise ImproperlyConfigured(
                "TemplateResponseMixin requires either a definition of "
                "'template_name' or an implementation of 'get_template_names()'")
        else:
            return ['flatpages/%s' % self.template_name]
