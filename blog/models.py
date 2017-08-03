from django.db import models
from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.shortcuts import reverse


class Author(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    class Meta:
        unique_together = (('first_name', 'last_name'), )

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)


class Post(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, default='', max_length=255)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='posts')
    content = RichTextField()
    image_url = models.URLField(max_length=600)
    metatags = models.ManyToManyField('Metatag', related_name='posts')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('blog-post', args=(self.slug, ))

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Post, self).save(*args, **kwargs)

    @property
    def content_preview(self):
        return self.content[:250]

    def __str__(self):
        return self.title


class Metatag(models.Model):
    tag = models.CharField(max_length=50)

    def __str__(self):
        return self.tag
