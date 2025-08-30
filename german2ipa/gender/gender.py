from .get_genders import get_genders


# Check to see if the word can be found in our dictionary
def get_gender_of_word(word, sentence: str = "", can_be_inf_verb: bool = True):
    genders = get_genders(word, sentence, can_be_inf_verb=can_be_inf_verb)

    # build the word_info dictionary
    if len(genders) > 0:
        grade = genders[0][-2]
        if grade == "L":  # from list
            certainty = 100
        elif grade == "A":  # absolutely sure
            certainty = 90
        elif grade == "C":  # copied
            certainty = 85
        elif grade == "G":  # guessing
            certainty = 80
        else:
            certainty = 0
        genders = [g[:2] for g in genders]

        return genders, certainty

    return [], 0
