import sys
import traceback
import operator


"""Useful nomads"""


def replace_multiple(value, map):
    return ''.join(map.get(s, s) for s in value)


def chunkify(lst, n):
    """Return array chunked into n-many pieces."""
    return [lst[i::n] for i in range(n)]


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


def handle_generic_exception():
    exc_info = sys.exc_info()
    traceback.print_exception(*exc_info)
    print("Unexpected error:", exc_info[0])


def traverse_and_compare(tree, comparison, obj, leaf_type):
    comparison_func = getattr(operator, comparison)
    for key, value in tree.items():
        if isinstance(value, leaf_type):
            # print('TraverseAndCompare: %s %s %s' % (value, comparison, getattr(obj, key)))
            if comparison_func(value, getattr(obj, key)):
                return True
        else:
            return traverse_and_compare(
                tree=value, comparison=comparison, obj=getattr(obj, key),
                leaf_type=leaf_type)
    return False


def numbers_only(string):
    new_string = ''
    passable_chars = '0123456789'
    for ch in filter_unmatched_gen(string, passable_chars):
        new_string += ch
    return new_string


def filter_unmatched_gen(a_collection, passable_items):
    for item in a_collection:
        if item in passable_items:
            yield item


def divide_or_zero(numerator, denominator):
    try:
        return numerator / denominator
    except ZeroDivisionError:
        return 0
