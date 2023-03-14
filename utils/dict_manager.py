def merge_dicts(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result

# exclude python dictionary properties


def exclude_dict_keys(d, keys):
    return {k: v for k, v in d.items() if k not in keys}
