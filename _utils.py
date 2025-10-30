from contextlib import contextmanager
from time import perf_counter

@contextmanager
def timed(msg='', width=25):
    start = perf_counter()
    yield
    stop = perf_counter()

    print(f'{msg:<{width}}elapsed \N{mathematical bold capital delta}{stop - start:.4f}s')
