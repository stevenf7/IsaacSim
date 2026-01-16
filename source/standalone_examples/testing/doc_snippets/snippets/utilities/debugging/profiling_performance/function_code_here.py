import carb


def some_function():
    # Some code that shouldn't be included in the profiler zone
    carb.profiler.begin(1, "zone title")
    # code to profile
    carb.profiler.end(1)
