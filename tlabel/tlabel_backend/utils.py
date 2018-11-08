import time
from functools import wraps


def timeit(f, name=None):
    @wraps(f)
    def kek(*args, **kwargs):
        start = time.time()
        method_name = name or f.__name__
        try:
            res = f(*args, **kwargs)
            exec_time = time.time() - start
            print('{method} in {exec_time} sec'.format(exec_time=exec_time, method=method_name))
        except:
            exec_time = time.time() - start
            print('{} FAILED in {} sec'.format(method_name, exec_time))
            raise

        return res

    return kek
