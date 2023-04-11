from django.views.generic.base import TemplateView


class AboutAuthorViews(TemplateView):
    template_name = 'about/author.html'


class AboutTechViews(TemplateView):
    template_name = 'about/tech.html'
