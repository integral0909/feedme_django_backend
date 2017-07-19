from django import forms
from django.contrib import admin
from django.urls import reverse
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.http.response import HttpResponseRedirect
from s3direct.widgets import S3DirectWidget
from data_entry.models import RecipeDraft, IngredientDraft


class RecipeDraftAdminForm(forms.ModelForm):
    checksum = forms.CharField(required=False)

    class Meta:
        fields = '__all__'
        model = RecipeDraft
        exclude = RecipeDraft.RAW_FIELDS
        widgets = {
            'image_url': S3DirectWidget(dest='raw-img')
        }


class IngredientDraftInline(admin.TabularInline):
    model = IngredientDraft
    can_delete = False
    readonly_fields = ('raw_text', 'checksum')
    extra = 0
    fields = ('ingredient', 'quantity', 'unit_type', 'preparation', 'fraction',
              'uses_fractions')


@admin.register(RecipeDraft)
class RecipeDraftAdmin(admin.ModelAdmin):
    change_form_template = 'publishable_change_form.html'
    form = RecipeDraftAdminForm
    list_display = ('__str__', 'seen', 'processed', 'published', 'source_url', 'image_url')
    search_fields = ('name_raw', 'source_url')
    inlines = [IngredientDraftInline]
    readonly_fields = ('checksum', 'created', 'updated') + RecipeDraft.RAW_FIELDS
    fieldsets = ((None, {'fields': (
                         ('name', 'name_raw'), ('description', 'description_raw'),
                         ('prep_time_seconds', 'prep_time_raw'),
                         ('cook_time_seconds', 'cook_time_raw'),
                         ('difficulty', 'difficulty_raw'), ('servings', 'servings_raw'),
                         ('image_url', 'image_url_raw'))
                        }),
                 ('Advanced', {'fields': ('recipe', ('seen', 'processed', 'published'),
                                          'checksum', 'source_url', ('created', 'updated')),
                               'classes': ('collapse',)}))

    def response_change(self, request, obj):
        if "_publish" in request.POST:
            form = self.form(request.POST)
            if form.is_valid():
                obj.publish()
            else:
                print(form.errors)
        if ("_addanother" in request.POST
           or '_continue' in request.POST
           or '_save' in request.POST):
            obj.processed = True
            obj.seen = True
            obj.save()
        return super(RecipeDraftAdmin, self).response_change(request, obj)


@admin.register(IngredientDraft)
class IngredientDraftAdmin(admin.ModelAdmin):
    pass