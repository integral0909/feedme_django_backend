from django import forms
from django.contrib import admin
from s3direct.widgets import S3DirectWidget
from data_entry.models import RecipeDraft, IngredientDraft


class RecipeDraftAdminForm(forms.ModelForm):
    class Meta:
        fields = '__all__'
        model = RecipeDraft
        widgets = {
            'image_url': S3DirectWidget(dest='raw-img')
        }


class IngredientDraftInline(admin.TabularInline):
    model = IngredientDraft
    classes = ('collapse', )
    can_delete = False
    readonly_fields = ('raw_text', 'checksum')
    fieldsets = (
        (None, {'fields': ('raw_text', 'ingredient', 'quantity', 'unit_type',
                           'ingredient_type', 'preparation', 'fraction', 'uses_fractions'),
                }),
        ('Advanced', {'fields': ('seen', 'processed', 'saved', 'recipe_ingredient'),
                      'classes': ('collapse',)}))


@admin.register(RecipeDraft)
class RecipeDraftAdmin(admin.ModelAdmin):
    change_form_template = 'publishable_change_form.html'
    form = RecipeDraftAdminForm
    list_display = ('name', 'source_url', 'image_url')
    search_fields = ('name', 'source_url')
    inlines = [IngredientDraftInline]
    readonly_fields = ('checksum', 'prep_time_raw', 'cook_time_raw', 'difficulty_raw')
    fieldsets = ((None, {'fields': (
                         'name', 'description', ('prep_time_raw', 'cook_time_raw'),
                         ('prep_time_seconds', 'cook_time_seconds'),
                         ('difficulty_raw', 'difficulty'), 'servings', 'source_url',
                         'image_url')
                        }),
                 ('Advanced', {'fields': ('recipe', ('seen', 'processed', 'saved'),
                                          'checksum'),
                               'classes': ('collapse',)}))

    def response_change(self, request, obj):
        opts = self.model._meta
        pk_value = obj._get_pk_val()
        preserved_filters = self.get_preserved_filters(request)

        if "_publish" in request.POST:
            obj.publish()
            redirect_url = reverse('admin:%s_%s_change' %
                                   (opts.app_label, opts.model_name),
                                   args=(pk_value,),
                                   current_app=self.admin_site.name)
            redirect_url = add_preserved_filters(
                {'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)
        else:
            return super(RecipeDraftAdmin, self).response_change(request, obj)


@admin.register(IngredientDraft)
class IngredientDraftAdmin(admin.ModelAdmin):
    pass