"""
Filename: get_genders.py
---
Author: TravisGK
Date: 29 August 2025

Description: This contains the function to return 
             a list of strings indicating a word's possible gender(s).

    Key:
        "v+" = infinitive verb singular using "das".
        "sm" = singular masculine.
        "sf" = singular feminine.
        "sn" = singular neutral.
        "pm" = plural masculine.
        "pf" = plural feminine.
        "pn" = plural neutral.
        "po" = plural-only.

        "(L)" = "list"; determined from text list (most reliable).
        "(A)" = "absolute"; follows a very consistent pattern.
        "(G)" = "guess"; follows somewhat consistent patterns (less reliable).

"""

import sys
from pathlib import Path

USE_V_PLUS_FOR_INFINITIVES = True
LISTS_DIR = Path(__file__).parent / "nouns"


def _load_words(article: str, singulars: list, plurals: list) -> None:
    file_path = LISTS_DIR / f"{article}.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            clean_line = line.strip().lower()
            elements = clean_line.split("\t")
            if elements[0] == "—" and len(elements) > 1:
                plurals.append(elements[1])
                continue

            singulars.append(elements[0])

            for element in elements[1:]:
                if element == "—":
                    break
                plurals.append(element)


_der_singulars = []
_der_plurals = []
_die_singulars = []
_die_plurals = []
_das_singulars = []
_das_plurals = []
_verbs_das = []
_plural_onlys = []


def _load_sets():
    global _der_singulars, _der_plurals
    global _die_singulars, _die_plurals
    global _das_singulars, _das_plurals
    global _verbs_das
    global _plural_onlys
    if len(_der_singulars) == 0:
        _load_words("der", _der_singulars, _der_plurals)
        _load_words("die", _die_singulars, _die_plurals)
        _load_words("das", _das_singulars, _das_plurals)
        _load_words("verbs-no-plural", _verbs_das, [])
        _load_words("plural-only", [], _plural_onlys)

        _der_singulars = set(_der_singulars)
        _der_plurals = set(_der_plurals)

        _die_singulars = set(_die_singulars)
        _die_plurals = set(_die_plurals)

        _das_singulars = set(_das_singulars)
        _das_plurals = set(_das_plurals)
        _verbs_das = set(_verbs_das)

        _plural_onlys = set(_plural_onlys)


def _find_results(
    word: str, grade: str, s_der, s_die, s_das, prior_chen: str, p_der, p_die, p_das
) -> list:
    results = []
    is_chen_word = False
    if word.endswith("chen") and word[-5] in prior_chen:
        results.append(f"sn({grade})")
        is_chen_word = True
    elif any(word.endswith(end) for end in s_der):
        results.append(f"sm({grade})")
    elif any(word.endswith(end) for end in s_die):
        results.append(f"sf({grade})")
    elif any(word.endswith(end) for end in s_das):
        results.append(f"sn({grade})")

    if is_chen_word:
        results.append(f"pn({grade})")
    elif any(word.endswith(end) for end in p_der):
        results.append(f"pm({grade})")
    elif any(word.endswith(end) for end in p_die):
        results.append(f"pf({grade})")
    elif any(word.endswith(end) for end in p_das):
        results.append(f"pn({grade})")

    return results


def _get_gender_by_absolutes(word: str) -> list:
    return _find_results(
        word=word,
        grade="A",  # absolute
        s_der=["ant", "ast", "eich", "ismus", "wert"],
        s_die=[
            "enz",
            "heit",
            "ie",
            "schaft",
            "sion",
            "tion",
            "tät",
            "ung",
            "macht",
            "firma",
        ],
        s_das=["lein", "ing", "ment", "tum", "thema", "schema"],
        prior_chen="dfghkmptvwxzß",
        p_der=["eiche", "ismen", "werte"],
        p_die=[
            "enzen",
            "heiten",
            "ien",
            "schaften",
            "sionen",
            "tionen",
            "täten",
            "ungen",
            "mächte",
            "firmen",
        ],
        p_das=["inge", "mente", "tümer", "themen", "schemen"],
    )


def _get_gender_by_guessing(word: str) -> list:
    return _find_results(
        word=word,
        grade="G",  # guessing
        s_der=["er", "ich", "ig", "eig", "or"],
        s_die=["anz", "ur"],
        s_das=["il", "ma", "nis"],
        prior_chen="n",
        p_der=["er", "oren"],
        p_die=["anzen", "uren"],
        p_das=["nisse"],
    )


def syllabify(word: str):
    """
    Heuristic syllabifier for German words.
    Returns a list of syllables (preserves original case).
    Not exhaustive: German syllabification has many exceptions.
    """
    w = word
    lower = w.lower()
    n = len(w)

    # vowels (including umlauts)
    vowels = set("aeiouyäöüy")
    # common diphthongs treated as single nucleus
    diphthongs = {"ie", "ei", "ai", "au", "äu", "eu", "ey", "oi", "ui", "ou"}
    # clusters that usually stay together and become onset of next syllable
    inseparable_clusters = {
        "sch",
        "ch",
        "ck",
        "ph",
        "th",
        "ng",
        "qu",
        "ts",
        "tz",
        "sp",
        "st",
        "sc",
        "pf",
        "tr",
        "dr",
        "kr",
        "gr",
        "pr",
        "br",
    }

    syllables = []
    i = 0
    while i < n:
        # find next vowel nucleus at or after i
        vpos = None
        for j in range(i, n):
            if lower[j] in vowels:
                vpos = j
                break
        if vpos is None:
            # no vowel left — attach remaining chars to last syllable or return as chunk
            if syllables:
                syllables[-1] += w[i:]
            else:
                syllables.append(w[i:])
            break

        # nucleus length (1 or 2 for diphthong)
        nucleus_len = 1
        if vpos + 1 < n and lower[vpos : vpos + 2] in diphthongs:
            nucleus_len = 2

        # find next vowel after this nucleus
        next_vpos = None
        for j in range(vpos + nucleus_len, n):
            if lower[j] in vowels:
                next_vpos = j
                break

        if next_vpos is None:
            # rest of word belongs to this final syllable
            syllables.append(w[i:])
            break

        # consonants between this nucleus and the next vowel
        cons_start = vpos + nucleus_len
        cons = lower[cons_start:next_vpos]

        if len(cons) == 0:
            # V V -> boundary before next vowel
            syll_end = cons_start
        elif len(cons) == 1:
            # V C V -> consonant moves to onset of next syllable
            syll_end = cons_start
        else:
            # multiple consonants: check inseparable clusters
            matched = False
            for cluster in sorted(inseparable_clusters, key=len, reverse=True):
                if cons.startswith(cluster):
                    matched = True
                    break
            if matched:
                # boundary before cluster (cluster goes to onset of next syllable)
                syll_end = cons_start
            else:
                # default: leave one consonant in coda, rest to next onset (VC.CV)
                syll_end = cons_start + 1

        syllables.append(w[i:syll_end])
        i = syll_end

    return syllables


def get_genders(word: str, sentence: str = "") -> list:
    """
    Returns a list of strings,
    each representing the kind of article the noun could have,
    along with a grade of certainty from the program itself.

    word (str): The noun to get the genders for.
    sentence (str): Optional. You can give the function the last ~5 words
                    and have it better infer what the noun's gender should be.

    Key:
        "v+" = infinitive verb singular using "das".
        "sm" = singular masculine.
        "sf" = singular feminine.
        "sn" = singular neutral.
        "pm" = plural masculine.
        "pf" = plural feminine.
        "pn" = plural neutral.
        "po" = plural-only.

        "(L)" = "list"; determined from text list (most reliable).
        "(A)" = "absolute"; follows a very consistent pattern.
        "(G)" = "guess"; follows somewhat consistent patterns (less reliable).
    """
    if not word[0].isalpha() or not word[0].isupper():
        return []

    word = word.lower()

    _load_sets()
    results = []

    if any(word.endswith(plural) for plural in _plural_onlys):
        return [
            "po(L)",
        ]

    is_infinitive = False
    if word in ["grunde"]:  # DATIV
        return [
            "sm(L)",
        ]

    if word in _der_singulars:
        results.append("sm(L)")
    if word in _die_singulars:
        results.append("sf(L)")
    if word in _das_singulars:
        results.append("sn(L)")
    if word in _verbs_das:
        is_infinitive = True  # has no specified plural.
        results.append("v+(L)" if USE_V_PLUS_FOR_INFINITIVES else "sn(L)")

    if word in _der_plurals:
        results.append("pm(L)")
    if word in _die_plurals:
        results.append("pf(L)")
    if not is_infinitive:
        if word in _das_plurals:
            results.append("pn(L)")

        if word in _plural_onlys:
            results.append("po(L)")

    if len(results) == 0:
        results = _get_gender_by_absolutes(word)
        if len(results) == 0:
            results = _get_gender_by_guessing(word)

    if len(results) == 0:
        # If there are still no results, chop away one character
        # at a time on the left side until results are met.
        # Stop doing this around 3 syllables left.
        syllables = syllabify(word)
        while len(syllables) > 1 and len(results) == 0:
            syllables = syllables[1:]
            search_term = "".join(syllables)
            print(search_term)
            search_term = search_term[0].upper() + search_term[1:]
            results = get_genders(search_term)

    if len(sentence) < len(word):
        return results

    # TODO: use contextual words to refine results.
    # Looks for contextual articles.
    MASC_TERMS = [
        f"{prep} {word}"
        for prep in ["bis", "durch", "gegen", "ohne", "um", "für"]
        for word in [
            "den",
            "einen",
            "seinen",
            "ihren",
            "Ihren",
            "unseren",
            "euren",
            "deinen",
            "meinen",
            "jeden",
            "eigenen",
        ]
    ]

    FEM_TERMS = [
        f"{prep} {word}"
        for prep in ["bis", "durch", "gegen", "ohne", "um", "für"]
        for word in ["eine", "jede", "jene"]
    ]

    FEM_OR_PLURAL_TERMS = [
        f"{prep} {word}"
        for prep in ["bis", "durch", "gegen", "ohne", "um", "für"]
        for word in [
            "die",
            "seine",
            "ihre",
            "Ihre",
            "unsere",
            "eure",
            "deine",
            "meine",
            "jede",
            "eigene",
        ]
    ]

    NEUTRAL_TERMS = [
        "das",
    ]
    MASC_OR_NEUTRAL_TERMS = [
        "dem",
        "einem",
    ]

    return results


def main():
    word = sys.argv[1] if len(sys.argv) > 1 else "Kaninchen"
    if word[0].islower():
        word = word[0].upper() + word[1:]
    print(get_genders(word))


if __name__ == "__main__":
    main()
