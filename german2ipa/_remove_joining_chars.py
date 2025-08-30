def remove_hyphens(german_text: str, replacement: str = ""):
    HYPHEN_CHAR = "+"
    hyphen_indices = []
    hyphen_word_indices = []
    inside_html = False

    i = 0
    while i < len(german_text):
        if i == 0 or i >= len(german_text) - 3:
            i += 1
            continue

        c = german_text[i]

        if not inside_html and german_text[i : i + 20].startswith("<span"):
            i += len("<span")
            inside_html = True
            continue
        elif inside_html and german_text[i] == ">":
            i += 1
            inside_html = False
            continue

        if not inside_html:
            prev_c = german_text[i - 1]
            current_c = german_text[i]
            next_c = german_text[i + 1]

            if prev_c.isalpha() and current_c == HYPHEN_CHAR and next_c.isalpha():
                hyphen_indices.append(i)

        i += 1

    de_words = german_text.split()  # split once, outside the loop
    for index in hyphen_indices:
        char_count = 0
        for i, word in enumerate(de_words):
            char_count += len(word)
            if char_count > index:
                # append the word index (0-based). add +1 for 1-based.
                hyphen_word_indices.append(i)  # or append(i+1) if you want 1-based
                break
            char_count += 1  # account for the single space

    for i in sorted(hyphen_indices, reverse=True):
        german_text = (
            german_text[:i]
            + replacement
            + (
                german_text[i + 1].upper()
                if len(replacement) > 0
                else german_text[i + 1]
            )
            + german_text[i + 2 :]
        )

    return german_text, hyphen_word_indices
