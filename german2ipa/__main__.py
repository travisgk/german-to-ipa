import sys
from ipa import german_to_ipa


def main():
    if len(sys.argv) < 2:
        print("Usage: python ipa.py <German_text> or <File_path>")
        sys.exit(1)

    german_text = " ".join(sys.argv[1:])
    if len(sys.argv[1:]) == 1 and ".txt" in german_text:  # is path.
        with open(german_text, "r", encoding="utf-8") as file:
            for line in file:
                german_text = line.strip()
                ipa = german_to_ipa(german_text)
                print(ipa, end="\n\n")
    else:
        ipa = german_to_ipa(german_text)
        print(ipa)


if __name__ == "__main__":
    main()
