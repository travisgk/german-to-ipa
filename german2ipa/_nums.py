def num_to_german(number: int):
    if number == 0:
        return "null"

    number = min(999999, number)

    LOW_NUMS = {
        1: "eins",
        2: "zwei",
        3: "drei",
        4: "vier",
        5: "fünf",
        6: "sechs",
        7: "sieben",
        8: "acht",
        9: "neun",
        10: "zehn",
        11: "elf",
        12: "zwölf",
        13: "dreizehn",
        14: "vierzehn",
        15: "fünfzehn",
        16: "sechzehn",
        17: "siebzehn",
        18: "achtzehn",
        19: "neunzehn",
    }
    TENS = {
        2: "zwanzig",
        3: "dreißig",
        4: "vierzig",
        5: "fünfzig",
        6: "sechzig",
        7: "siebzig",
        8: "achtzig",
        9: "neunzig",
    }

    result = ""
    thousands_digit = number // 1000
    if thousands_digit > 0:
        if thousands_digit > 19:
            prefix = num_to_german(thousands_digit)
        else:
            if thousands_digit == 1:
                prefix = "ein"
            else:
                prefix = LOW_NUMS[thousands_digit]

        result += f"{prefix}tausend"
        number -= thousands_digit * 1000

    hundreds_digit = number // 100
    if hundreds_digit > 0:
        if hundreds_digit == 1:
            prefix = "ein"
        else:
            prefix = LOW_NUMS[hundreds_digit]

        result += f"{prefix}hundert"
        number -= hundreds_digit * 100

    tens_digit = number // 10
    ones_digit = number % 10

    if tens_digit <= 1:
        result += LOW_NUMS[number]
    else:
        if ones_digit == 1:
            prefix = "ein"
        else:
            prefix = LOW_NUMS[ones_digit]
        suffix = TENS[tens_digit]
        result += f"{prefix}und{suffix}"

    return result


def replace_nums_with_german(german: str) -> str:
    words = german.split(" ")
    for word_i, word in enumerate(words):
        if word[0].isdigit():
            last_digit_i = len(word) - 1
            for i in range(len(word) - 1, -1, -1):
                if word[i].isdigit():
                    last_digit_i = i
                    break
            num_str = word[0 : last_digit_i + 1]
            german = num_to_german(int(num_str))
            words[word_i] = german + word[last_digit_i + 1 :]
    german = " ".join(words)

    return german
