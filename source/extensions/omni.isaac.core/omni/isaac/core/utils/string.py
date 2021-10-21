def find_unique_string_name(intitial_name, is_unique_fn):
    if is_unique_fn(intitial_name):
        return intitial_name
    iterator = 1
    result = intitial_name + "_" + str(iterator)
    while not is_unique_fn(result):
        result = intitial_name + "_" + str(iterator)
        iterator += 1
    return result
