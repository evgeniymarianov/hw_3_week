def row_label(row_number: int) -> str:
    label = ""
    value = row_number
    while value > 0:
        value, remainder = divmod(value - 1, 26)
        label = chr(ord("A") + remainder) + label
    return label or "A"
