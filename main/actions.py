import csv
from django.http import StreamingHttpResponse


class Echo(object):
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def export_as_csv_action(description="Export selected objects as CSV file",
                         fields=None, exclude=None, header=True):
    """
    This function returns an export csv action
    'fields' and 'exclude' work like in django ModelForm
    'header' is whether or not to output the column names as the first row
    """
    def export_as_csv(modeladmin, request, queryset):
        """
        Generic csv export admin action.
        based on http://djangosnippets.org/snippets/1697/
        """
        opts = modeladmin.model._meta
        field_names = set(field.name for field in opts.fields)
        if fields:
            fieldset = set(fields)
            field_names = fieldset
        elif exclude:
            excludeset = set(exclude)
            field_names = field_names - excludeset

        def gen():
            yield list(field_names)
            for obj in queryset.iterator():
                row = []
                for field in field_names:
                    attr = getattr(obj, field)
                    v = attr() if callable(attr) else attr
                    row.append(v)
                yield row

        def streamer(writer):
            for row in gen():
                yield writer.writerow(row)

        writer = csv.writer(Echo())
        response = StreamingHttpResponse(streamer(writer),
                                         content_type="text/csv")
        cd = 'attachment; filename={}.csv'.format(str(opts).replace('.', '_'))
        response['Content-Disposition'] = cd
        return response
    export_as_csv.short_description = description
    return export_as_csv
