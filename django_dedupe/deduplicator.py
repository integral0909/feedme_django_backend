from django.db.models import Count
from django.db import IntegrityError, connection
from django.contrib.postgres.aggregates.general import ArrayAgg
from common.utils.async import run_chunked_iter


class Deduplicator(object):
    """Deduplicates a model based on some field comparison while maintaining foreign keys."""
    queryset = None
    model = None
    fieldname = None
    field_func = None
    exclude_relations = []

    def __init__(self, queryset=None, fieldname=None, model=None, field_func=None,
                 exclude_relations=None):
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
        self.exclude_relations = exclude_relations or self.exclude_relations

    def get_aware_queryset(self):
        """Returns a queryset consisting of a count of duplicates and associated id's"""
        _field = self.fieldname
        qs = self.queryset.values(self.fieldname)
        if self.field_func:
            qs = qs.annotate(_field=self.field).values('_field')
            _field = '_field'

        return qs.annotate(_duplicate_count=Count(_field)-1, _ids=ArrayAgg('id'))\
                 .filter(_duplicate_count__gte=1)

    def get_naive_queryset(self):
        """Returns the deduplicator's unmodified queryset"""
        return self.queryset

    def get_aware_list(self):
        """Returns a list of objects with the unique value, duplicate count, and list of ids"""
        if not hasattr(self, 'process_item'):
            return list(self.get_aware_queryset())

        return self._build_aware_list()

    def _build_aware_list(self):
        """
        If a callable named `process_item` is declared on the deduplicator then
        this method is called to build a list of duplicate aware dictionaries.
        """
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
        def worker(items):
            for i in items:
                self.dedupe_item(i)
            connection.close()
        run_chunked_iter(self.get_aware_list(), worker)

    def _add_related_counters(self, obj):
        """Adds a count of related references, used to determine the master"""
        obj._related_ref_count = 0
        for field in (self.m2m_fields + self.related_fields):
            try:
                obj._related_ref_count += getattr(obj, field.name).count()
            except AttributeError:
                pass
        return obj

    def dedupe_item(self, item):
        """Deduplicate a set of duplicate rows as listed in item"""
        qs = self.model.objects.filter(id__in=item['_ids'])
        objs = sorted([self._add_related_counters(obj) for obj in qs],
                      key=lambda obj: obj._related_ref_count)
        master = objs.pop()
        for replica in objs:
            self.disconnect_replica(master, replica)
        master.save()

    def disconnect_replica(self, master, replica):
        """Disconnects a replica from its related fields and re-attaches them to the master"""
        for field in (self.related_fields + self.m2m_fields):
            if field.name in self.exclude_relations:
                continue
            try:
                for rel in getattr(replica, field.name).all():
                    try:
                        f = getattr(master, field.name)
                    except AttributeError:
                        pass
                    else:
                        try:
                            f.add(rel)
                        except IntegrityError as e:
                            print(e)
            except AttributeError:
                pass
        replica.delete()


