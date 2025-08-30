#!/usr/bin/env python3
"""
File: ipa.py

Description: This script wraps around the eSpeak function's output
             and improves the IPA output from the German language option.

Author: TravisGK
Date: 2025 August 21

pip install phonemizer regex espeakng

"""

import os
import regex as re
from _remove_joining_chars import remove_joining_chars
from _nums import replace_nums_with_german

if os.name == "nt":  # on Windows.
    # Put this before importing phonemize or before the first phonemize() call
    from phonemizer.backend.espeak.wrapper import EspeakWrapper

    # change this to the actual location on your machine
    dll_path = r"C:\Program Files\eSpeak NG\libespeak-ng.dll"

    EspeakWrapper.set_library(dll_path)
else:
    # optional: set a custom .so/.dylib path if needed
    # os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = "/usr/lib/x86_64-linux-gnu/libespeak-ng.so.1"
    pass

from phonemizer import phonemize


PUNCTUATION = ".,,:?;!\"'-[]‘„“«»…"

# matches Latin letters (any accents) OR characters from common IPA blocks/diacritics
PAT = re.compile(
    r"""[
        \p{Script=Latin}\p{Letter}          # latin letters (incl. accents)
        \p{Block=IPA_Extensions}           # U+0250..02AF
        \p{Block=Spacing_Modifier_Letters} # U+02B0..02FF (many phonetic modifiers)
        \p{Block=Combining_Diacritical_Marks}           # U+0300..036F
        \p{Block=Combining_Diacritical_Marks_Extended}  # U+1AB0..1AFF
        \p{Block=Phonetic_Extensions}                  # U+1D00..1D7F
        \p{Block=Phonetic_Extensions_Supplement}       # U+1D80..1DBF
        \p{Block=Modifier_Tone_Letters}                # U+A700..A71F
    ]""",
    re.VERBOSE,
)


def keep_latin_and_ipa(s: str) -> str:
    return "".join(PAT.findall(s))


def remove_parentheses(text: str) -> str:
    # Remove all content inside parentheses, including the parentheses
    return re.sub(r"\([^()]*\)", "", text)


def remove_punctuation(s: str) -> str:
    for c in PUNCTUATION:
        s = s.replace(c, "")
    return s


def break_ipa_by_r(ipa: str) -> list:
    results = [e for e in re.split(r"([Rɐʁɾrɜ])", ipa) if len(e) > 0]

    combined = []
    for part in results:
        if len(combined) > 0 and any(part.startswith(c) for c in "Rɐʁɾrɜ"):
            if combined[-1].endswith("r"):
                combined.append(part)
            else:
                combined[-1] = combined[-1] + part
        else:
            combined.append(part)

    return combined


def break_word_by_r(word: str) -> list:
    results = [e for e in re.split(r"([Rr])", word) if len(e) > 0]
    combined = []
    for part in results:
        if len(combined) > 0 and part.startswith("r"):
            combined[-1] = combined[-1] + part
        else:
            combined.append(part)
    return combined


def german_to_ipa(german: str) -> str:
    # R and Y are placeholders.
    REMOVE_EXCESSIVE_STRESSES = True
    COLLAPSE_SCHWAS = True  # IPA wise: Rasen -> Ras'n
    MOVE_STRESSES_BEFORE_CONSONANTS = True

    VOICELESS_SCHWA = ""
    SILENT_LETTER_L = "ḷ"
    SILENT_LETTER_N = "ṇ"
    SILENCING_CONSONANTS = "bçdfɡkpsʃtvxz"
    CONSONANTS = "Rbxçdfɡjkll̩mm̩nn̩ŋpzsʃtvʔʒ"
    VOWELS = "Yaɛeɪiɔoœøʊuʏyə"
    MAYBE_LONG_IPA = "Yaɛ"
    ALWAYS_LONG_IPA = "eioøuy"

    # Convert any numbers into German words.
    german = replace_nums_with_german(german)

    german, hyphen_word_indices = remove_joining_chars(german, " ")

    ipa = phonemize(
        german,
        language="de",
        backend="espeak",  # uses espeak backend
        strip=True,
        preserve_punctuation=True,
        with_stress=True,
    )

    ipa = ipa.replace("ɛsɪst", "ɛs ɪst")
    ipa = ipa.replace("ɑ", "a")

    archived_ipa = ipa

    orig_words = german.split(" ")
    ipa_words = ipa.split(" ")

    if len(orig_words) != len(ipa_words):
        print("ERROR: `orig_words` and `ipa_words` have mismatching lengths.")
        print(orig_words)
        print(ipa_words)
        return ""

    results = []
    for orig, ipa in zip(orig_words, ipa_words):
        orig = remove_punctuation(orig)
        word_is_capitalized = orig[0].isupper()
        orig = orig.lower()

        if orig == "unsere":
            results.append("ʊnzəʁə")
            continue  # to next word.
        elif orig == "deren":
            results.append("deːʁən")
            continue
        elif orig == "hing":
            results.append("hɪŋ")
            continue

        ipa = remove_parentheses(ipa)
        ipa = remove_punctuation(ipa)

        old_ipa = ipa

        # Append the index of every vowel char that *could* be long.
        maybe_is_long = []
        for i, c in enumerate(ipa):
            if c in MAYBE_LONG_IPA:
                maybe_is_long.append(i < len(ipa) - 1 and ipa[i + 1] == "ː")

        # Remove stress markers and add a placeholder for a common IPA pattern.
        terms = [("ɛɾ", "YR"), ("ː", ""), ("ˈ", ""), ("ˌ", "")]
        for term, replacement in terms:
            ipa = ipa.replace(term, replacement)

        orig = keep_latin_and_ipa(orig)
        ipa = keep_latin_and_ipa(ipa)

        if len(orig) == 0:
            continue

        # Do baseline replacements.
        if ipa.endswith("ɾ"):
            ipa = ipa[:-1] + "ɐ"

        ipa = ipa.replace("ɜ", "ɐ")
        ipa = ipa.replace("ɔø", "ɔɪ")

        pattern = rf"(?<=[{CONSONANTS}])([ɐʁɾrɜ])(?=[{CONSONANTS}])"
        ipa = re.sub(pattern, "ɐ", ipa)

        pattern = rf"(?<=[{CONSONANTS}])([ɐʁɾrɜ])(?![{CONSONANTS}])"
        ipa = re.sub(pattern, "ʁ", ipa)

        pattern = rf"(?<=[{VOWELS}])([ɐʁɾrɜ])(?=[{CONSONANTS}])"
        ipa = re.sub(pattern, "ʁ", ipa)

        if ipa.endswith("ʁ"):
            ipa = ipa[:-1] + "ɐ"

        if word_is_capitalized:
            if orig.endswith("ende") and ipa.endswith("əndə"):
                ipa = ipa[:-4] + "ʔɛndə"
            elif orig.endswith("endes") and ipa.endswith("əndəs"):
                ipa = ipa[:-4] + "ʔɛndəs"

        if len(ipa) >= 5:
            if any(ipa.startswith(l) for l in ["fɛʁ", "fYR"]):
                ipa = "fɛɐ" + ipa[3:]
            elif any(ipa.startswith(l) for l in ["ɛʁ", "YR"]):
                ipa = "ɛɐ" + ipa[2:]

        # Break the word apart by any R characters.
        words_parts = break_word_by_r(orig)
        ipa_parts = break_ipa_by_r(ipa)
        if len(words_parts) == len(ipa_parts):
            if words_parts[-1].endswith("er") and ipa_parts[-1].endswith("YR"):
                ipa_parts[-1] = ipa_parts[-1][:-2] + "eɐ"

            for i, (word_part, ipa_part) in enumerate(zip(words_parts, ipa_parts)):
                # Check for various ways a word piece ending with R
                # can specifically end.
                if "är" in word_part:
                    for key in ["er", "YR", "ɛr"]:
                        ipa_parts[i] = ipa_parts[i].replace(key, "ɛɐ")

                elif word_part.endswith("ver") and i < len(words_parts):
                    matched = False
                    for key in ["fer", "fYR", "fɛr"]:
                        if key in ipa_parts[i]:
                            ipa_parts[i] = ipa_parts[i].replace(key, "fɛɐ")
                            matched = True
                    if matched and i > 0:
                        prev_part = ipa_parts[i - 1]
                        if any(prev_part.endswith(l) for l in ["ɛʁ", "YR"]):
                            ipa_parts[i - 1] = prev_part[:-2] + "ɐ"

                elif word_part.endswith("vor") and i < len(words_parts):
                    matched = False
                    for key in ["fɔɐ", "foʁ"]:
                        if key in ipa_parts[i]:
                            ipa_parts[i] = ipa_parts[i].replace(key, "foɐ")
                            matched = True
                    if matched and i > 0:
                        prev_part = ipa_parts[i - 1]
                        if any(prev_part.endswith(l) for l in ["ɛʁ", "YR"]):
                            ipa_parts[i - 1] = prev_part[:-2] + "ɐ"

            orig = "".join(words_parts)
            ipa = "".join(ipa_parts)
        else:
            print("ERROR: `orig_parts` and `ipa_parts` have mismatching lengths.")
            print(words_parts)
            print(ipa_parts)
            return ""

        ipa = ipa.replace("hɪŋ", "hɪnɡ")
        ipa = ipa.replace("aʊsç", "aʊsʃ")
        ipa = ipa.replace("eʁd", "eɐd")
        ipa = ipa.replace("YRd", "eɐd")
        ipa = ipa.replace("ɛʁst", "ɛɐst")
        ipa = ipa.replace("eʁst", "eɐst")
        ipa = ipa.replace("eʁt", "eɐt")
        ipa = ipa.replace("YRst", "eɐst")
        ipa = ipa.replace("YRt", "eɐt")
        ipa = ipa.replace("r", "ʁ")
        ipa = ipa.replace("ɾh", "ɐh")
        ipa = ipa.replace("YR", "ɛʁ")
        ipa = ipa.replace("ɾ", "ʁ")  # defaults

        pattern = rf"(ɔɪʁ)(?=[{CONSONANTS}])"
        ipa = re.sub(pattern, "ɔɪɐ", ipa)

        pattern = rf"(lɔs)(?=[dfgjklmnpqrvxzçl̩m̩n̩ʃʔ])"
        ipa = re.sub(pattern, "los", ipa)

        pattern = rf"(lɔsts)(?=[{VOWELS}])"
        ipa = re.sub(pattern, "los", ipa)

        ipa = ipa.replace("vɐdən", "veɐdən")
        ipa = ipa.replace("ɛɐvaxz", "ɛɐvaks")

        """


        Put the long vowel char back.
        """
        for char in ALWAYS_LONG_IPA:
            ipa = ipa.replace(char, f"{char}ː")

        if any(maybe_is_long):
            parts = []
            last_i = 0
            maybe_i = 0
            for i, c in enumerate(ipa):
                if c in MAYBE_LONG_IPA:
                    if maybe_is_long[maybe_i]:
                        parts.append(ipa[last_i : i + 1] + "ː")
                    else:
                        parts.append(ipa[last_i : i + 1])
                    maybe_i += 1
                    last_i = i + 1
            if last_i < len(ipa):
                parts.append(ipa[last_i:])
            ipa = "".join(parts)

        """


        Starting patterns. (term/replacement)
        """
        terms = [
            ("aʊfɛʁ", "aʊfʔɛɐ"),
            ("apɛʁ", "aːbɐ"),
            ("anɛʁ", "anʔɛɐ"),
            ("aneːɐ", "anʔɛɐ"),
            ("ʊnɛʁ", "ʊnʔɛɐ"),
            ("aʊsɛʁ", "aʊsʔɛɐ"),
            ("mɪtɛʁ", "mɪtʔɛɐ"),
            ("foːʁɛʁ", "foːɐʔɛɐ"),
            ("ɛʁoːb", "ɛɐʔoːb"),
            ("bəaɪ", "bəʔaɪ"),
        ]
        for term, replacement in terms:
            if ipa.startswith(term):
                ipa = replacement + ipa[len(term) :]

        def replace_start(
            txt: str,
            term: str,
            replacement: str,
            next_chars: list,
        ) -> str:
            """
            Returns the `txt with the `term` replaced with the `replacement`,
            but the original `term` is only replaced
            if the following char in the `txt` is in the given `next_chars`.
            """
            if (
                len(txt) > len(term)
                and txt.startswith(term)
                and txt[len(term)] in next_chars
            ):
                txt = replacement + txt[len(term) :]
            return txt

        ipa = replace_start(ipa, "foːʁ", "foːɐ", next_chars=CONSONANTS + "ʁ")
        ipa = replace_start(ipa, "ɛmpɔʁ", "ɛmpoːɐ", next_chars=CONSONANTS + "ʁ")
        ipa = replace_start(ipa, "yːbʁ", "yːbɐ", next_chars=CONSONANTS + "ʁ")
        ipa = replace_start(ipa, "yːbʁ", "yːbɐʔ", next_chars=VOWELS)
        ipa = replace_start(ipa, "ʊntʁ", "ʊntɐ", next_chars=CONSONANTS + "ʁ")
        ipa = replace_start(ipa, "ʊntʁ", "ʊntɐʔ", next_chars=VOWELS)

        if orig.startswith("zer"):
            if ipa.startswith("tseːɐtiːfi"):
                ipa = "tsɛʁtifi" + ipa[10:]
            elif ipa.startswith("tsɛʁ"):
                ipa = "tsɛɐ" + ipa[4:]
        elif orig.startswith("hervor") and any(ipa.startswith(l) for l in ["hɐfoːɐ"]):
            ipa = "hɛɐfoːɐ" + ipa[6:]
        elif orig.startswith("der"):
            for key in ["deːʁ", "dɛːʁ", "dɛʁ"]:
                if ipa.startswith(key):
                    ipa = "deːɐ" + ipa[len(key) :]
                    break
        elif orig.startswith("ernst") and ipa.startswith("ɛɐnst"):
            ipa = "ɛʁnst" + ipa[5:]
        elif orig.startswith("fuß") and ipa.startswith("fʊs"):
            ipa = "fuːs" + ipa[3:]

        if (
            len(orig) > 5
            and orig.endswith("haft")
            and orig[-5] != "c"
            and ipa[-4] != "h"
            and ipa.endswith("aft")
        ):
            ipa = ipa[:-3] + "haft"
        elif orig.endswith("tuch") and ipa.endswith("tʊx"):
            ipa = ipa[:-3] + "tuːx"
        elif orig.endswith("tücher") and ipa.endswith("tʏçɐ"):
            ipa = ipa[:-4] + "tyçɐ"
        elif orig.endswith("tüchern") and ipa.endswith("tʏçɐn"):
            ipa = ipa[:-5] + "tyçɐn"
        elif ipa[:-1].endswith("ɛɐk"):
            ipa = ipa[:-4] + "ɛʁk" + ipa[-1]
        elif ipa.endswith("ɪɡtən"):
            ipa = ipa[:-5] + "ɪçtən"
        elif ipa[:-1].endswith("ɪɡt"):
            ipa = ipa[:-4] + "ɪçt" + ipa[-1]
        elif ipa.endswith("ɪɡt"):
            ipa = ipa[:-3] + "ɪçt"
        """


        Put the primary and secondary stresses back.
        """
        primary_indices = []
        secondary_indices = []

        for i, c in enumerate(old_ipa):
            if c == "ˈ":
                primary_indices.append(i)
            elif c == "ˌ":
                secondary_indices.append(i)

        def find_before(indices: list) -> list:
            """
            Returns a list of indices
            where a stress char should be added before.
            """
            add_before = []
            for i in indices:
                before = old_ipa[i - 1] if i - 1 >= 0 else None
                after = old_ipa[i + 1] if i + 1 < len(old_ipa) else None

                start_j = max(0, i - 1)
                end_j = min(len(ipa) - 1, i + 1)
                for j in range(start_j, end_j + 1):
                    if ipa[j] == "ː":
                        continue

                    c_before_j = ipa[j - 1] if j >= 0 else None
                    c_after_j = ipa[j] if j < len(ipa) else None
                    offset = 0

                    if c_before_j == "ː":
                        c_before_j = ipa[j - 2] if j - 2 >= 0 else None

                    elif c_after_j == "ː":
                        if j + 1 < len(ipa):
                            c_after_j = ipa[j + 1]
                            offset = 1
                        else:
                            c_after_j = None

                    if (before == c_before_j and before is not None) or (
                        after == c_after_j and after is not None
                    ):
                        add_before.append(j + offset)
                        break

            return add_before

        add_primary_before = find_before(primary_indices)
        add_secondary_before = find_before(secondary_indices)
        for i in sorted(add_primary_before, reverse=True):
            ipa = ipa[:i] + "ˈ" + ipa[i:]

        add_secondary_before = [
            i + len([p_i for p_i in add_primary_before if p_i <= i])
            for i in add_secondary_before
        ]

        for i in sorted(add_secondary_before, reverse=True):
            ipa = ipa[:i] + "ˌ" + ipa[i:]

        if REMOVE_EXCESSIVE_STRESSES:
            if ipa.startswith("ˌ"):
                ipa = ipa[1:]
            if len(add_primary_before) == 1 and len(add_secondary_before) == 0:
                first_vowel_indices = []
                in_vowels = False
                for i, c in enumerate(ipa):
                    if c in VOWELS:
                        if not in_vowels:
                            in_vowels = True
                            first_vowel_indices.append(i)
                    else:
                        in_vowels = False

                if len(first_vowel_indices) > 0:
                    primary_index = ipa.find("ˈ")
                    if primary_index == first_vowel_indices[0] - 1:
                        ipa = ipa[:primary_index] + ipa[primary_index + 1 :]

        if MOVE_STRESSES_BEFORE_CONSONANTS:
            primary_indices = [i for i, c in enumerate(ipa) if c == "ˈ"]
            secondary_indices = [i for i, c in enumerate(ipa) if c == "ˌ"]
            if len(primary_indices) > 0 or len(secondary_indices) > 0:
                primary_indices.reverse()
                secondary_indices.reverse()

                def move_indices_back(indices: list) -> list:
                    results = indices[:]
                    first_vowel_index = next(
                        (i for i, c in enumerate(ipa) if c in VOWELS), -1
                    )
                    for i in range(len(results)):
                        while results[i] > 0 and (
                            results[i] < first_vowel_index
                            or (
                                ipa[results[i] - 1] == "ʃ"
                                and ipa[results[i]] in "ʁtvlp"
                            )
                            or (
                                results[i] > 1
                                and ipa[results[i] - 2] == "ʃ"
                                and ipa[results[i] - 1 : results[i] + 1]
                                in ["tʁ", "pl", "pʁ"]
                            )
                            or (
                                ipa[results[i] - 1 : results[i] + 1]
                                in ["ts", "pf", "dʒ"]
                            )
                            or (
                                ipa[results[i]] not in CONSONANTS + "h"
                                and ipa[results[i] - 1] in CONSONANTS + "ʁh"
                            )
                        ):
                            results[i] -= 1

                    return sorted(list(set(results)), reverse=True)

                primary_indices_to = move_indices_back(primary_indices)
                secondary_indices_to = move_indices_back(secondary_indices)

                for start, end in zip(primary_indices, primary_indices_to):
                    ipa = ipa[:start] + ipa[start + 1 :]
                    ipa = ipa[:end] + "ˈ" + ipa[end:]

                for start, end in zip(secondary_indices, secondary_indices_to):
                    ipa = ipa[:start] + ipa[start + 1 :]
                    ipa = ipa[:end] + "ˌ" + ipa[end:]

                if REMOVE_EXCESSIVE_STRESSES:
                    if ipa.startswith("ˌ") or (
                        len(primary_indices_to) == 1
                        and len(secondary_indices_to) == 0
                        and ipa.startswith("ˈ")
                    ):
                        ipa = ipa[1:]

        ipa = ipa.replace("ˈviːdeːˌɔ", "ˈviːdeoːˌ")
        ipa = ipa.replace("viːdeːoː", "viːdeoː")
        ipa = ipa.replace("taʊzʔɛnd", f"taʊz{VOICELESS_SCHWA}{SILENT_LETTER_N}d")
        ipa = ipa.replace("vɛɐm", "vɛʁm")

        if COLLAPSE_SCHWAS:
            if len(ipa) >= 3 and ipa[-2:] == "ən" and ipa[-3] in SILENCING_CONSONANTS:
                ipa = ipa[:-2] + VOICELESS_SCHWA + SILENT_LETTER_N
            elif len(ipa) >= 3 and ipa[-2:] == "əl" and ipa[-3] in SILENCING_CONSONANTS:
                ipa = ipa[:-2] + VOICELESS_SCHWA + SILENT_LETTER_L
            elif (
                len(ipa) >= 4
                and ipa[-3:-1] == "əl"
                and ipa[-1] in "nt"
                and ipa[-4] in SILENCING_CONSONANTS
            ):
                ipa = ipa[:-3] + VOICELESS_SCHWA + SILENT_LETTER_L + ipa[-1]

            if not word_is_capitalized:
                ENDS = [
                    "ənt",
                    "əndə",
                    "əndɐ",
                    "əndən",
                    "əndəs",
                    "əlnt",
                    "əlndə",
                    "əlndɐ",
                    "əlndən",
                    "əlndəs",
                ]
                for end in ENDS:
                    if (
                        len(end) < len(ipa)
                        and ipa.endswith(end)
                        and ipa[-len(end) - 1] in SILENCING_CONSONANTS
                    ):
                        if end[1] == "l":
                            ipa = (
                                ipa[: -len(end)]
                                + VOICELESS_SCHWA
                                + SILENT_LETTER_L
                                + "n"
                                + end[3:]
                            )
                        else:
                            ipa = (
                                ipa[: -len(end)]
                                + VOICELESS_SCHWA
                                + SILENT_LETTER_N
                                + end[2:]
                            )
                        break
        results.append(ipa)

    # Restore punctuation.
    old_results = archived_ipa.split(" ")
    if len(results) == len(old_results):
        for i, (old, new) in enumerate(zip(old_results, results)):
            if any(old.endswith(c) for c in PUNCTUATION):
                results[i] = new + old[-1]

    result = ""
    for i, r in enumerate(results):
        result += r
        if i < len(results) - 1:
            if i in hyphen_word_indices:
                if r[-1] == "ɐ" and results[i + 1][0] in VOWELS:
                    result += "ʔ"

            else:
                result += " "

    return result
