# german2ipa
This command line script converts German next into the International Phonetic Alphabet (IPA) by improving eSpeak's phonetic outputs.
The outputs should more closely resemble those seen on Wiktionary.

## Setup
```pip install phonemizer regex espeakng```

## Usage

```py german2ipa "In der Beschränkung zeigt sich erst der Meister."```

Prints:
![ɪn deːɐ bəʃʁˈɛnkʊŋ tsaɪkt zɪç eːɐst deːɐ maɪstɐ.](result.png)

You can also have it transcribe a file of German text line-by-line.
```py german2ipa mytext.txt```
