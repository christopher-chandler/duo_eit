# Standard
import time

# Pip
# None

# Custom
# None


def measure_func_exec_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        if duration < 1:
            print(f"{func.__name__} executed in {duration * 1000:.4f} ms")
        else:
            print(f"{func.__name__} executed in {duration:.4f} s")
        return result

    return wrapper


def post_progress(arg1):
    def actual_decorator(func):
        def wrapper(*args, **kwargs):
            print(arg1)
            return func(*args, **kwargs)

        return wrapper

    return actual_decorator
