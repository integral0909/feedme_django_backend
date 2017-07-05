from django.contrib import admin
from django import forms
from django.conf import settings
from blog.models import *
from s3direct.widgets import S3DirectWidget
from better_filter_widget import BetterFilterWidget


def _get_cdn_image(data):
    return '%s%s' % (settings.CDN_URL, data.get('image_url', '').split('/')[-1:][0])


class PostForm(forms.ModelForm):
    class Meta:
        fields = '__all__'
        model = Post
        widgets = {
            'image_url': S3DirectWidget(dest='raw-img'),
            'metatags': BetterFilterWidget,
        }

    def save(self, commit=True):
        obj = super(PostForm, self).save(commit=False)
        obj.image_url = _get_cdn_image(self.cleaned_data)
        if commit:
            obj.save()
            self.save_m2m()
        return obj


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostForm
    list_display = ('__str__', 'content_preview', 'author', 'created')
    list_filter = ('author', )
    search_fields = ('title', 'content')
    # readonly_fields = ('slug', )
    prepopulated_fields = {"slug": ("title",)}


admin.site.register(Author)
admin.site.register(Metatag)
