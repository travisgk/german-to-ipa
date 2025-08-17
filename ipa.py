#!/usr/bin/env python3
"""
File: ipa.py

Description: This script wraps around the eSpeak function's output
             and improves the IPA output from the German language option.

Author: TravisGK
Date: 2025 August 16

pip install phonemizer regex espeakng

"""

import os
import sys
import regex as re

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


PUNCTUATION = ".,:?;!\"'-[]‘„“«»…"


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
    CONSONANTS = "Rbxçdfɡjkll̩mm̩nn̩ŋpzsʃtvʔʒ"
    VOWELS = "Yaɛeɪiɔoœøʊuʏyə"
    MAYBE_LONG_IPA = "Yaɛ"
    ALWAYS_LONG_IPA = "eioøuy"

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
        orig = remove_punctuation(orig).lower()
        ipa = remove_punctuation(ipa)

        old_ipa = ipa

        maybe_is_long = []
        for i, c in enumerate(ipa):
            if c in MAYBE_LONG_IPA:
                maybe_is_long.append(i < len(ipa) - 1 and ipa[i + 1] == "ː")

        terms = [("ɛɾ", "YR"), ("ː", ""), ("ˈ", ""), ("ˌ", "")]
        for term, replacement in terms:
            ipa = ipa.replace(term, replacement)

        orig = keep_latin_and_ipa(orig)
        ipa = keep_latin_and_ipa(ipa)

        if len(orig) == 0:
            continue

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

        if len(ipa) >= 5:
            if any(ipa.startswith(l) for l in ["fɛʁ", "fYR"]):
                ipa = "fɛɐ" + ipa[3:]
            elif any(ipa.startswith(l) for l in ["ɛʁ", "YR"]):
                ipa = "ɛɐ" + ipa[2:]

        words_parts = break_word_by_r(orig)
        ipa_parts = break_ipa_by_r(ipa)
        if len(words_parts) == len(ipa_parts):
            if words_parts[-1].endswith("er") and ipa_parts[-1].endswith("YR"):
                ipa_parts[-1] = ipa_parts[-1][:-2] + "eɐ"

            for i, (word_part, ipa_part) in enumerate(zip(words_parts, ipa_parts)):
                if "är" in word_part:
                    for key in ["er", "YR", "ɛr"]:
                        ipa_parts[i] = ipa_parts[i].replace(key, "ɛɐ")

                elif word_part.endswith("ver") and i < len(words_parts) - 1:
                    matched = False
                    for key in ["fer", "fYR", "fɛr"]:
                        ipa_parts[i] = ipa_parts[i].replace(key, "fɛɐ")
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

        ipa = ipa.replace("eʁd", "eɐd")
        ipa = ipa.replace("YRd", "eɐd")
        ipa = ipa.replace("eʁt", "eɐt")
        ipa = ipa.replace("YRt", "eɐt")
        ipa = ipa.replace("r", "ʁ")
        ipa = ipa.replace("ɾh", "ɐh")
        ipa = ipa.replace("YR", "ɛʁ")

        pattern = rf"(ɔɪʁ)(?=[{CONSONANTS}])"
        ipa = re.sub(pattern, "ɔɪɐ", ipa)

        # Put the long vowel char back.
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

        # Put the primary and secondary stresses back.
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

        results.append(ipa)

    # Restore punctuation.
    old_results = archived_ipa.split(" ")
    if len(results) == len(old_results):
        for i, (old, new) in enumerate(zip(old_results, results)):
            if any(old.endswith(c) for c in PUNCTUATION):
                results[i] = new + old[-1]

    return " ".join(results)


def main():
    if len(sys.argv) < 2:
        print("Usage: python ipa.py <German_text>")
        sys.exit(1)

    german_text = " ".join(sys.argv[1:])
    ipa = german_to_ipa(german_text)
    print(ipa)


if __name__ == "__main__":
    main()
