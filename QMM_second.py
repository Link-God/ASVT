from sympy.logic import simplify_logic
from sympy.logic import to_dnf
import numpy as np
import itertools
from prettytable import PrettyTable
import re


def read_func_from_file(file_name):
    """
    Функция считывает из файла наборы на которых булева функция истина и возвращает их как список
    :param file_name: Имя файла
    :return: Список наборов на которых БФ = Истина
    """
    with open(file_name) as f:
        return sorted([line.strip() for line in f.readlines()])


def check_make_implicant(minterm1, minterm2):
    """
    Функция возвращает пару, первый элемент - истина если можно объединить минтермы в импликант, иначе - ложь
    Второй элемент - индекс элемента по которому можно произвести объединение
    :param minterm1: Первый минтерм
    :param minterm2: Второй минтерм
    :return: Пара bool (можно объеденить), int(где объеденить)
    """
    counter = 0
    index = -1
    can_make = False
    for i, (ch1, ch2) in enumerate(zip(minterm1, minterm2)):
        if ch1 != ch2:
            counter += 1
            index = i
            can_make = True
        if counter > 1:
            can_make = False
            return can_make, -1
    return can_make, index


# noinspection PyShadowingNames
def make_implicants_from_function(func):
    """
    Функция по списку истинных значений возвращает список импликант, комбинирование которых невозможно
    :param func:Список истиннных значений БФ
    :return:Список финальных испликант
    """
    cur_level_implicants = func[:]
    was_made_concatenation = True
    final_implicants = []
    while was_made_concatenation:
        next_level_implicants = []
        was_made_concatenation = False
        was_used = set()
        for i, minterm1 in enumerate(cur_level_implicants):
            used = False
            for minterm2 in cur_level_implicants[i + 1:]:
                can_concatenate, index = check_make_implicant(minterm1, minterm2)
                if can_concatenate:
                    was_used.add(minterm2)
                    used = True
                    was_made_concatenation = True
                    implicant = minterm1[:index] + '~' + minterm1[index + 1:]
                    if implicant not in next_level_implicants:
                        next_level_implicants.append(implicant)
            if not used \
                    and minterm1 not in was_used \
                    and '~' in minterm1 \
                    and minterm1 not in final_implicants:
                final_implicants.append(minterm1)
        cur_level_implicants = next_level_implicants
    return final_implicants


def nums_from_implicant(implicant):
    """
    Вспомогательная функция оформления
    Возвращает отсортированный список всех значений которые может содержать в себе имликант
    Пример: 1~1 -> 101=5, 111=7 -> [5, 7]
    :param implicant: Импликант
    :return: Сортированный список "защифрованных значений"
    """
    result = []

    def num_in_imp(imp: str, res: list):
        tild_index = imp.find('~')
        if tild_index == -1:
            res.append(imp)
        else:
            num_in_imp(imp[:tild_index] + '0' + imp[tild_index + 1:], res)
            num_in_imp(imp[:tild_index] + '1' + imp[tild_index + 1:], res)

    num_in_imp(implicant, result)
    return sorted([int(x, base=2) for x in result])


def make_matrix(list_of_nums_in_row, columns):
    """
    Функция создает таблицу простых импликант (https://w.wiki/UK7 см тут шаг 2)
    :param list_of_nums_in_row: Список позиций для каждой строки.
     Позиция означает что импликант покрывает набор соответствующий столбцу
    :param columns: Список столбцов, то есть десятичные представления наборов на которых функция истнинна
    :return: Матрица простых импликантов
    """
    res_matrix = []
    for i in range(len(list_of_nums_in_row)):
        row = [1 if num in list_of_nums_in_row[i] else 0 for num in columns]
        res_matrix.append(row)
    return res_matrix


def get_kernel_row_indexes(mat):
    """
    Функция ищет и возвращает индексы строк ядра матрицы простых импликант
    :param mat: Матрица простых импликант
    :return: Индексы строк ядра
    """
    swap_matrix = mat.swapaxes(0, 1)
    indexes = set()
    for j, arr in enumerate(swap_matrix):
        if np.count_nonzero(arr == 1) == 1:
            indexes.add(np.where(arr == 1)[0][0])
    return indexes


def get_kernel_col_indexes(mat, row_indexes):
    """
    Функция ищет и возвращает индексы столбцов ядра матрицы простых импликант
    :param mat: Матрица простых импликант
    :param row_indexes: Индексы строк ядра
    :return: Индексы столбцов ядра
    """
    indexes = set()
    for row in (row for i, row in enumerate(mat) if i in row_indexes):
        columns = set(np.where(row == 1)[0])
        indexes.update(columns)
    return indexes


def create_matrix_without_kernel(mat, row, col):
    """
    Функция создает и возвращает матрицу простых импликант без ядра
    :param mat: Имхрдная матрица
    :param row: Индексы строк ядра
    :param col: Индексы столбцов ядра
    :return: Матрица без ядра
    """
    res_mat = np.array(mat)
    res_mat = np.delete(res_mat, list(row), axis=0)
    res_mat = np.delete(res_mat, list(col), axis=1)
    return res_mat


def delete_zero_rows(mat):
    """
    Функция удаляет нулевые строки у матрицы
    :param mat: Матрица
    :return: Матрица без нулевых строк
    """
    rows_num = np.where(~mat.any(axis=1))[0]
    return np.delete(mat, rows_num, axis=0), set(rows_num)


def pretty_table_to_file(file_name, mat, impls, terms):
    """
    Функция печатает "красивую таблицу в файл"
    :param file_name: Имя файла
    :param mat: Матрица
    :param impls: Импликанты
    :param terms: Наборы на которых БФ = истина
    :return:
    """
    table = PrettyTable()
    table.field_names = ['impl'] + sorted(terms)
    for implicant, row in zip(impls, mat):
        table.add_row([implicant] + list(str(x) for x in row))
    with open(file_name, 'w') as f:
        f.write(str(table))


def petrick_method(mat, else_impls):
    """
    Функция реализует метод Петрика (см https://w.wiki/UKB)
    (Метод Петрика — метод для получения всех минимальных ДНФ из таблицы простых импликант)
    Помогает получить финальный ответ после учета и отбрасывания ядра таблицы простых импликант
    :param mat: Таблица протсых импикант без ядра
    :param else_impls: Оставшиеся испликанты
    :return: Минимальное покрытие таблицы состоящее из импликантов
    """
    symbols_tup = tuple(chr((ord('a') + i)) for i in range(len(mat)))
    col_mat = mat.swapaxes(0, 1)
    cnf = ['(' + ' | '.join(itertools.compress(symbols_tup, col)) + ')' for col in col_mat]
    mul_of_cnf = ' & '.join(cnf)
    sim_dnf = str(to_dnf(simplify_logic(mul_of_cnf)))
    min_combo = re.sub(r'[()\s]', '', sim_dnf[:sim_dnf.find('|')]).split('&')
    add_implicants = [else_impls[ord(ch) - ord('a')] for ch in min_combo]
    return add_implicants


if __name__ == '__main__':
    """
    Аналог main() в C++
    Вызывает необходимые функции в нужно порядке, делая некторые дополнительные манипуляции с временными переменными
    """
    file_with_func = 'my.txt'
    func = read_func_from_file(file_with_func)
    list_of_true_numbers = sorted([int(term, base=2) for term in func])
    implicants = make_implicants_from_function(func)
    implicants_with_nums = [(implicant, nums_from_implicant(implicant)) for implicant in implicants]
    matrix = np.array(
        make_matrix([tup[1] for tup in implicants_with_nums], list_of_true_numbers))
    pretty_table_to_file('out0_my.txt', matrix, implicants, func)
    kernel_row_indexes = get_kernel_row_indexes(matrix)
    kernel_col_indexes = get_kernel_col_indexes(matrix, kernel_row_indexes)
    implicants_from_MDNF = [implicants[i] for i in kernel_row_indexes]
    matrix_without_kernel = create_matrix_without_kernel(matrix, kernel_row_indexes, kernel_col_indexes)
    matrix_without_kernel, zero_row = delete_zero_rows(matrix_without_kernel)
    else_implicants_with_zero_rows = [implicant for i, implicant in enumerate(implicants)
                                      if i not in kernel_row_indexes]
    else_implicants = [implicant for i, implicant in enumerate(else_implicants_with_zero_rows)
                       if i not in zero_row]
    else_terms = [term for i, term in enumerate(sorted(func)) if i not in kernel_col_indexes]
    pretty_table_to_file('out1_my.txt', matrix_without_kernel, else_implicants, else_terms)
    additional_implicants = petrick_method(matrix_without_kernel, else_implicants)
    print(implicants_from_MDNF, additional_implicants)
