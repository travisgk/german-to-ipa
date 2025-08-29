import sys
import pyperclip
from ipa import PUNCTUATION, remove_punctuation, german_to_ipa
from gender.gender import get_gender_of_word
from _remove_hyphens import remove_hyphens


def process_sentence(german_text: str, color_by_gender: bool):
    DER_SPAN = '<span class="der-noun">'
    DIE_SPAN = '<span class="die-noun">'
    DAS_SPAN = '<span class="das-noun">'
    PLURAL_DER_SPAN = '<span class="plural-der-noun">'
    PLURAL_DIE_SPAN = '<span class="plural-die-noun">'
    PLURAL_DAS_SPAN = '<span class="plural-das-noun">'
    PLURAL_ONLY_SPAN = '<span class="plural-only-noun>'
    SINGULAR_INFINITIVE_SPAN = '<span class="verb-no-plural-noun">'
    german_text = german_text.strip()
    full_ipa = german_to_ipa(german_text)
    words = german_text.split()
    transcriptions = full_ipa.split()

    word_results = []
    ipa_results = []

    if color_by_gender and len(words) == len(transcriptions):
        SKIPPED_TERMS = [
            "ich",
            "du",
            "er",
            "wir",
            "sie",
            "ihr",
            "ihm",
            "ihn",
            "ihnen",
            "ihren",
            "sein",
            "seinen",
            "seine",
            "ihre",
            "es",
            "das",
            "der",
            "die",
            "und",
            "aber",
            "noch",
            "ein",
            "eine",
            "eines",
            "einer",
            "einen",
            "einem",
        ]
        for i, (word, ipa) in enumerate(zip(words, transcriptions)):
            word = word.strip()
            no_punctuation = remove_punctuation(word).strip()
            if (
                word[0].isalpha()
                and word[0].isupper()
                and not no_punctuation.lower() in SKIPPED_TERMS
            ):  # noun.
                genders, confidence = get_gender_of_word(no_punctuation)
                if len(genders) == 0:
                    if no_punctuation.endswith("n"):
                        new_genders, new_confidence = get_gender_of_word(
                            no_punctuation[:-1]
                        )
                        if new_confidence >= 80:
                            genders, confidence = new_genders, new_confidence
                    elif no_punctuation.endswith("es"):
                        new_genders, new_confidence = get_gender_of_word(
                            no_punctuation[:-2]
                        )
                        if new_confidence >= 80 and any(
                            g[:2] in ["sm", "sn"] for g in new_genders
                        ):
                            genders, confidence = (
                                new_genders,
                                new_confidence,
                            )  # assumed genitiv.
                    elif no_punctuation.endswith("s"):
                        new_genders, new_confidence = get_gender_of_word(
                            no_punctuation[:-1]
                        )
                        if new_confidence >= 80 and any(
                            g[:2] in ["sm", "sn", "v+"] for g in new_genders
                        ):
                            genders, confidence = (
                                new_genders,
                                new_confidence,
                            )  # assumed genitiv.

                is_plural = len(genders) > 0 and genders[0].startswith("p")

                if len(genders) == 0:
                    span = None
                elif not is_plural and confidence < 80:
                    span = None
                elif genders[0] == "v+":
                    span = SINGULAR_INFINITIVE_SPAN
                elif genders[0][1] == "m":
                    span = PLURAL_DER_SPAN if is_plural else DER_SPAN
                elif genders[0][1] == "f":
                    span = PLURAL_DIE_SPAN if is_plural else DIE_SPAN
                elif genders[0][1] == "n":
                    span = PLURAL_DAS_SPAN if is_plural else DAS_SPAN
                elif genders[0][1] == "o":
                    span = PLURAL_ONLY_SPAN
                else:
                    span = None

                if span is None:
                    word_results.append(word)
                    ipa_results.append(ipa)
                else:
                    puncts = ""
                    while any(word.endswith(c) for c in PUNCTUATION):
                        puncts += word[-1]
                        word = word[:-1]
                    while any(ipa.endswith(c) for c in PUNCTUATION):
                        ipa = ipa[:-1]
                    word_results.append(f"{span}{word}</span>{puncts}")
                    ipa_results.append(f"{span}{ipa}</span>{puncts}")
            else:
                word_results.append(word)
                ipa_results.append(ipa)

        words_str = " ".join(word_results)
        ipa_str = " ".join(ipa_results)
        words_str, _ = remove_hyphens(words_str, "")
        return (words_str, ipa_str)

    """ Get rid of hyphens. """

    german_text, _ = remove_hyphens(german_text, "")

    return (german_text, full_ipa)


def get_lines_from_clipboard() -> list:
    in_clipboard = pyperclip.paste().strip()
    for char in ["\n", ". ", "! ", "? "]:
        in_clipboard = in_clipboard.replace(char, f"{char}ſ")

    lines = in_clipboard.split("ſ")
    return lines


def main():
    save_to_file = False
    if len(sys.argv) < 2:
        print("Usage: python ipa.py <German_text> or <File_path>.")
        print("\t-v to use clipboard's contents")
        print("\t-x to write results to clipboard.")
        sys.exit(1)

    else:
        german_text = " ".join(sys.argv[1:])
        to_clipboard = False
        from_clipboard = False
        color_by_gender = False

        if "--html" in german_text:
            german_text = german_text.replace("--html", "")
            color_by_gender = True
        if "-vx " in german_text or german_text.endswith("-vx"):
            german_text = german_text.replace("-vx", "")
            from_clipboard = True
            to_clipboard = True

        elif "-xv " in german_text or german_text.endswith("-xv"):
            german_text = german_text.replace("-xv", "")
            from_clipboard = True
            to_clipboard = True
        else:
            if "-v " in german_text or german_text.endswith("-v"):
                german_text = german_text.replace("-v", "")
                from_clipboard = True

            if "-x " in german_text or german_text.endswith("-x"):
                german_text = german_text.replace("-x", "")
                to_clipboard = True

        german_text = german_text.replace("  ", " ").strip()
        if from_clipboard:
            lines = get_lines_from_clipboard()
        elif len(sys.argv[1:]) == 1 and ".txt" in german_text:  # is path.
            with open(german_text, "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file]
                save_to_file = True
        else:
            lines = [
                german_text,
            ]

    results = [
        process_sentence(line, color_by_gender=color_by_gender) for line in lines
    ]
    word_lines, ipa_lines = zip(*results)
    word_lines = list(word_lines)
    ipa_lines = list(ipa_lines)

    def lines_to_str(lines: list) -> str:
        if len(lines) == 1:
            return lines[0]

        html = "<ul>\n"
        for i, line in enumerate(lines):
            html += f"<li>{line}</li>\n"
        html += "</ul>"

        return html

    word_str = lines_to_str(word_lines)
    ipa_str = lines_to_str(ipa_lines)

    print(word_str, end="\n\n")
    print(ipa_str)

    if to_clipboard:
        copy_str = word_str + "\n\n" + ipa_str
        pyperclip.copy(copy_str)

    elif save_to_file:
        with open("mytext-ipa.txt", "w", encoding="utf-8") as file:
            for result in results:
                file.write(result + "\n")


if __name__ == "__main__":
    main()
