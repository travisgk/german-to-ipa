from .get_genders import get_genders


# Check to see if the word can be found in our dictionary
def get_gender_of_word(word):
    genders = get_genders(word)

    # build the word_info dictionary
    if len(genders) > 0:
        grade = genders[0][-2]
        if grade == "L":
            certainty = 100
        elif grade == "A":
            certainty = 90
        elif grade == "G":
            certainty = 80
        else:
            certainty = 0

        genders = [g[:2] for g in genders]

        return genders, certainty

    return [], 0
