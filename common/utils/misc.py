import sys
import traceback


"""Useful nomads"""


def replace_multiple(value, map):
    return ''.join(map.get(s, s) for s in value)


def chunkify(lst, n):
    return [lst[i::n] for i in range(n)]


def handle_generic_exception():
    exc_info = sys.exc_info()
    traceback.print_exception(*exc_info)
    print("Unexpected error:", exc_info[0])
