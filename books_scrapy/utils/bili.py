def biligen(id):
    table = "fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF"
    indices = [9, 8, 1, 6, 2, 4]
    x = (id ^ 177451812) + 8728348608
    result = list(f"1  4 1 7  ")
    for i in range(len(indices)):
        result[indices[i]] = table[x // 58 ** i % 58]
    return "".join(result)
