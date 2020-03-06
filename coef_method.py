from itertools import chain, combinations
from pprint import pp


def powerset(n):
    s = range(n)
    return chain.from_iterable(combinations(s, r) for r in range(1, len(s) + 1))


def read_func_from_file(file_name):
    with open(file_name) as f:
        return sorted([line.strip() for line in f.readlines()])


def create_coef_for_equation(num, n):
    num_base2_as_str = bin(num)[2:].rjust(n, '0')
    equation = set()
    for tup in powerset(n):
        down_index = ''.join(str(x) for x in tup)
        up_index = ''.join(num_base2_as_str[i] for i in tup)
        equation.add((down_index, up_index))
    return equation


def create_system(f):
    set_of_true_nums = {int(num, base=2) for num in f}
    n = len(f[0])
    dict_sys = {num: (True if num in set_of_true_nums else False, create_coef_for_equation(num, n)) for num in
                range(2 ** n)}
    return dict_sys


def creat_set_of_zero_coef(sys):
    res_set = set()
    for tup in sys.values():
        if not tup[0]:
            res_set.update(tup[1])
    return res_set


def delete_false_from_system(sys):
    set_key_for_del = set()
    for kye, (val, _) in sys.items():
        if not val:
            set_key_for_del.add(kye)
    for key in set_key_for_del:
        sys.pop(key)


def delete_zero_coef_from_system(sys, zeros):
    for key, (bool_val, cur_set) in sys.items():
        new_set = cur_set - zeros
        sys[key] = (bool_val, new_set)


def get_final_coef_from_system(sys: dict):
    res = []
    sort_key = sorted([k for k in sys.keys()], key=lambda k: len(sys[k][1]))
    for i, key in enumerate(sort_key):
        if sys.get(key, None) is None:
            continue
        min_len = len(min(sys[key][1], key=lambda tup: len(tup[0]))[0])
        all_min_el = [el for el in sys[key][1] if len(el[0]) == min_len]
        min_el = all_min_el[0]
        if len(all_min_el) != 1:
            max_in_other = 0
            cur_el_in_other = 0
            for el in all_min_el:
                for other_key in sort_key[i + 1:]:
                    if sys.get(other_key, None) is None:
                        continue
                    if el in sys[other_key][1]:
                        cur_el_in_other += 1
                if cur_el_in_other > max_in_other:
                    min_el = el
                    max_in_other = cur_el_in_other
        res.append(min_el)
        keys_for_delete = {key for key, (_, coef) in sys.items() if min_el in coef}
        for k in keys_for_delete:
            sys.pop(k)
    return res


if __name__ == '__main__':
    file_with_func = 'func.txt'
    func = read_func_from_file(file_with_func)
    system = create_system(func)
    set_of_zero_coef = creat_set_of_zero_coef(system)
    delete_false_from_system(system)
    delete_zero_coef_from_system(system, set_of_zero_coef)
    final_coef = get_final_coef_from_system(system)
    pp(final_coef)
