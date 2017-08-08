from django.db.models import Count, Max, Q
from django.db.models.functions import Lower
from django.contrib.postgres.aggregates.general import ArrayAgg


class Deduplicator(object):
    """Deduplicates a model based on some field comparison while maintaining foreign keys."""
    queryset = None
    model = None
    fieldname = None
    field_func = None

    def __init__(self, queryset=None, fieldname=None, field_func=None, model=None):
        self.queryset = queryset or self.queryset
        self.model = model or self.model
        self.fieldname = fieldname or self.fieldname
        self.field_func = field_func or self.field_func
        self.field = self.field_func(self.fieldname) if self.field_func else self.fieldname
        self.related_fields = [f for f in self.model._meta.get_fields()
                               if (f.one_to_many or f.one_to_one)
                               and f.auto_created and not f.concrete]
        self.m2m_fields = [f for f in self.model._meta.get_fields()
                               if f.many_to_many and not f.auto_created]

    def get_aware_queryset(self):
        return self.queryset.values(self.fieldname).annotate(_field=self.field)\
                   .values('_field').annotate(_duplicate_count=Count('_field')-1,
                                              _ids=ArrayAgg('id'))\
                   .filter(_duplicate_count__gte=1)

    def get_naive_queryset(self):
        return self.queryset

    def get_aware_list(self):
        if not hasattr(self, 'process_item'):
            return list(self.get_aware_queryset())

        return self._build_aware_list()

    def _build_aware_list(self):
        aware_list = []
        value_hash = {}
        for item in self.get_naive_queryset():
            val = self.process_item(item)
            idx = value_hash.get(val)
            try:
                dupe = aware_list[idx]
            except IndexError:
                dupe = {'_ids': [], '_duplicate_count': -1, '_field': val}
            dupe['_ids'].append(item.id)
            dupe['_duplicate_count'] += 1
            if not idx:
                aware_list.append(dupe)
                value_hash[val] = len(aware_list)-1
        return aware_list

    def __call__(self, *args, **kwargs):
        self.dedupe()

    def dedupe(self):
        duped = self.get_aware_list()
        for item in duped:
            self.dedupe_item(item)

    def _add_related_counters(self, obj):
        obj.related_count = 0
        for field in self.m2m_fields:
            obj.related_count += len(getattr(obj, field.name))
        for field in self.related_fields:
            getattr(obj, field.name)
            obj.related_count += len(getattr(obj, field.name).all())
        print(obj, obj.related_count)
        return obj

    def dedupe_item(self, item):
        qs = self.model.objects.filter(id__in=item['_ids'])
        objs = [self._add_related_counters(obj) for obj in qs]
        print(objs)







