from django.contrib import admin
from django import forms
from blog.models import *
from s3direct.widgets import S3DirectWidget
from better_filter_widget import BetterFilterWidget


class PostForm(forms.ModelForm):
    class Meta:
        fields = '__all__'
        model = Post
        widgets = {
            'image_url': S3DirectWidget(dest='raw-img'),
            'metatags': BetterFilterWidget,
        }


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
