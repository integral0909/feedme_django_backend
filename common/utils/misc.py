import sys
import traceback
import operator


"""Useful nomads"""


def replace_multiple(value, map):
    return ''.join(map.get(s, s) for s in value)


def chunkify(lst, n):
    return [lst[i::n] for i in range(n)]


def handle_generic_exception():
    exc_info = sys.exc_info()
    traceback.print_exception(*exc_info)
    print("Unexpected error:", exc_info[0])


def traverse_and_compare(tree, comparison, obj, leaf_type):
    print('In traverse and compare')
    comparison_func = getattr(operator, comparison)
    for key, value in tree.items():
        print(key,value)
        if isinstance(value, leaf_type):
            print('TraverseAndCompare: %s %s %s' % (value, comparison, getattr(obj, key)))
            if comparison_func(value, getattr(obj, key)):
                return True
        else:
            traverse_and_compare(
                tree=value, comparison=comparison, obj=getattr(obj, key),
                leaf_type=leaf_type)
    return False
