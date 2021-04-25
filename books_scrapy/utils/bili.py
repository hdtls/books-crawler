def biligen(id):
    table = "fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF"
    indices = [11, 10, 3, 8, 4, 6]
    x = (id ^ 177451812) + 8728348608
    result = list("CM1  4 1 7  ")
    for i in range(len(indices)):
        result[indices[i]] = table[x // 58 ** i % 58]
    return "".join(result)
