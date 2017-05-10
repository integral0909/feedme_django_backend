from common.utils import chunkify
import threading


"""Helpers for threaded programming"""


def threaded(fn):
    """Decorator for executing a function in a new thread."""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper


def run_chunked_iter(iterable_item, worker_func, args=None, num_threads=8):
    """
    Split the provided iterable into chunks, process each chunk in a separate thread
    """
    threads = []
    chunked_iterables = chunkify(iterable_item, num_threads)
    for chunk in chunked_iterables:
        main_args = [chunk]
        if isinstance(args, (list, tuple, set)) is True:
            main_args = main_args + list(args)
        t = threading.Thread(target=worker_func, args=main_args)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
