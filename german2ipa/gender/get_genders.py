"""
Filename: get_genders.py
---
Author: TravisGK
Date: 30 August 2025

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
        "(C)" = "copied"; copied from another spelling.
        "(G)" = "guess"; follows somewhat consistent patterns (less reliable).

"""

import sys
from pathlib import Path

NOUN_JOINING_CHAR = "+"

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
_weak_der_singulars = []
_weak_der_declinations = []
_plural_onlys = []


def _load_sets():
    global _der_singulars, _der_plurals
    global _die_singulars, _die_plurals
    global _das_singulars, _das_plurals
    global _verbs_das
    global _weak_der_singulars, _weak_der_declinations
    global _plural_onlys
    if len(_der_singulars) == 0:
        _load_words("der", _der_singulars, _der_plurals)
        _load_words("die", _die_singulars, _die_plurals)
        _load_words("das", _das_singulars, _das_plurals)
        _load_words("verbs-no-plural", _verbs_das, [])
        _load_words(
            "der-special-declinations",
            _weak_der_singulars,
            _weak_der_declinations,
        )
        _load_words("plural-only", [], _plural_onlys)

        _der_singulars = set(_der_singulars)
        _der_plurals = set(_der_plurals)

        _die_singulars = set(_die_singulars)
        _die_plurals = set(_die_plurals)

        _das_singulars = set(_das_singulars)
        _das_plurals = set(_das_plurals)
        _verbs_das = set(_verbs_das)
        _weak_der_singulars = set(_weak_der_singulars)
        _weak_der_declinations = set(_weak_der_declinations)
        _plural_onlys = set(_plural_onlys)


def _find_results(
    word: str, grade: str, s_der, s_die, s_das, prior_chen: str, p_der, p_die, p_das
) -> list:
    results = []
    is_chen_word = False
    if len(word) >= 5 and word.endswith("chen") and word[-5] in prior_chen:
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
            "keit",
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
            "keiten",
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
        s_der=["ich", "eig", "or"],
        s_die=["anz", "ur"],
        s_das=["il", "ma", "nis"],
        prior_chen="n",
        p_der=["oren"],
        p_die=["anzen", "uren"],
        p_das=["nisse"],
    )


def _syllabify(word: str):
    """
    Heuristic syllabifier for German words.
    Returns a list of syllables (preserves original case).
    Uses a whitelist of valid German onsets to avoid illegal onsets
    like "rr" or "ck" being placed at a syllable start.
    """
    w = word
    lower = w.lower()
    n = len(w)

    # vowels (including umlauts and ß-safe)
    vowels = set("aeiouyäöüy")
    diphthongs = {"ie", "ei", "ai", "au", "äu", "eu", "ey", "oi", "ui", "ou"}

    # clusters that usually stick together (treat as possible onsets)
    inseparable_clusters = {
        "sch",
        "ch",
        "ph",
        "ng",
        "qu",
        "ts",
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
        "str",
        "spr",
        "skr",
        "kn",
        "gn",
        "tsch",
    }

    # Common valid German onsets (single + common clusters).
    # This list is not linguistically exhaustive but covers usual onsets.
    valid_onsets = {
        # single consonants
        "b",
        "c",
        "d",
        "f",
        "g",
        "h",
        "j",
        "k",
        "l",
        "m",
        "n",
        "p",
        "q",
        "r",
        "s",
        "t",
        "v",
        "w",
        "z",
        # 2-letter clusters
        "bl",
        "br",
        "cl",
        "cr",
        "dr",
        "fl",
        "fr",
        "gl",
        "gr",
        "pl",
        "pr",
        "tr",
        "kr",
        "kn",
        "gn",
        "pf",
        "ph",
        "ts",
        "qu",
        "sp",
        "st",
        "sc",
        "sm",
        "sn",
        "sr",
        # 3+ letter clusters (common)
        "sch",
        "str",
        "spr",
        "skr",
        "tsch",
    }

    # explicit illegal onsets (safety net)
    illegal_onsets = {
        "rr",
        "ck",
        "zz",
        "kk",
        "tz",
    }  # expand if you see other wrong cases

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
            # no vowel: attach remainder to last syllable (or create one)
            if syllables:
                syllables[-1] += w[i:]
            else:
                syllables.append(w[i:])
            break

        # detect diphthong length
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
            # last syllable: everything to end
            syllables.append(w[i:])
            break

        cons_start = vpos + nucleus_len
        cons = lower[cons_start:next_vpos]  # consonant cluster between vowels

        # --- Decide coda_len using whitelist-first approach ---
        if len(cons) == 0:
            coda_len = 0
        else:
            coda_len = None
            # Try maximal onset principle constrained by valid_onsets/inseparable_clusters.
            # We iterate s from 0 .. len(cons)-1; onset = cons[s:]; choose largest onset present.
            for s in range(0, len(cons)):
                onset = cons[s:]
                if onset in inseparable_clusters or onset in valid_onsets:
                    coda_len = s
                    break

            # fallback heuristics if no exact onset match found
            if coda_len is None:
                if len(cons) == 1:
                    # single consonant goes to onset (ba-ken)
                    coda_len = 0
                else:
                    # default: leave one consonant as onset (maximal onset fallback)
                    coda_len = max(0, len(cons) - 1)

            # safety: if the chosen onset would be an illegal cluster (rr, ck, ...),
            # push all consonants to coda (so onset becomes empty or smaller)
            onset = cons[coda_len:]
            if onset in illegal_onsets:
                coda_len = len(cons)

        syll_end = cons_start + coda_len
        syllables.append(w[i:syll_end])
        i = syll_end

    # special-case: -zen ending often joins previous syllable (e.g., "Flötzen" patterns)
    if len(syllables) > 1 and syllables[-1].lower() == "zen":
        last = syllables.pop()
        syllables[-1] = syllables[-1] + last

    return syllables


def get_genders(word: str, sentence: str = "", can_be_inf_verb: bool = True) -> list:
    """
    Returns a list of strings,
    each representing the kind of article the noun could have,
    along with a grade of certainty from the program itself.

    word (str): The noun to get the genders for.
    sentence (str): Optional. You can give the function the last ~5 words
                    and have it better infer what the noun's gender should be.
    can_be_inf_verb (bool): If True, a word can be identified as "v+".
                            This is set to False when recursing.

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
        "(C)" = "copied"; copied from another spelling.
        "(G)" = "guess"; follows somewhat consistent patterns (less reliable).
    """
    if not word[0].isalpha() or not word[0].isupper():
        return []

    word = word.lower()

    _load_sets()
    results = []

    flag = "L" if can_be_inf_verb else "C"

    if any(word.endswith(plural) for plural in _plural_onlys):
        return [
            f"po({flag})",
        ]

    is_infinitive = False
    if word in ["grunde"]:  # DATIV
        return [
            f"sm({flag})",
        ]
    elif word == "herzen":
        return [
            f"sn({flag})",
            f"pn({flag})",
        ]
    elif word in ["herzens", "herzes"]:
        return [
            f"sn({flag})",
        ]

    if word in _der_singulars:
        results.append(f"sm({flag})")
    if word in _die_singulars:
        results.append(f"sf({flag})")
    if word in _das_singulars:
        results.append(f"sn({flag})")

    if word in _der_plurals:
        if (
            all(t not in results for t in ["sm(L)", "sm(C)"])
            and word in _weak_der_declinations
        ):
            results.append(f"sm({flag})")
        results.append(f"pm({flag})")
    if word in _die_plurals:
        results.append(f"pf({flag})")

    if word not in _verbs_das:
        if word in _das_plurals:
            results.append(f"pn({flag})")

        if word in _plural_onlys:
            results.append(f"po({flag})")

    elif can_be_inf_verb:  # is infinitive.
        results.append(f"v+({flag})" if USE_V_PLUS_FOR_INFINITIVES else f"sn({flag})")

    if len(results) == 0:
        results = _get_gender_by_absolutes(word)
        if len(results) == 0:
            results = _get_gender_by_guessing(word)

    if len(results) == 0:
        # If there are still no results, chop away one character
        # at a time on the left side until results are met.
        # Stop doing this around 1 syllables left.
        subwords = word.split(NOUN_JOINING_CHAR)
        syllables = [s for w in subwords for s in _syllabify(w)]
        while len(syllables) > 1 and len(results) == 0:
            syllables = syllables[1:]
            search_term = "".join(syllables)
            search_term = search_term[0].upper() + search_term[1:]
            if len(search_term) <= 3:
                break
            results = get_genders(search_term, can_be_inf_verb=False)

    if len(sentence) < len(word) or len(results) <= 1:
        return results

    prev_words = sentence.split()
    if prev_words[-1] == word:
        prev_words = prev_words[:-1]

    first_noun_i = next(
        (
            len(prev_words) - i - 1
            for i, w in enumerate(reversed(prev_words))
            if w[0].isupper() and w[0].isalpha
        ),
        -1,
    )
    if first_noun_i >= 0:
        prev_words = prev_words[first_noun_i + 1 :]

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
