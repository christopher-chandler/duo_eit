# Standard
# None

# Pip
# None

# Custom
from duo.duo_parser import DuoParser


if __name__ == "__main__":
    duo_path = "/Users/christopherchandler/code_repos/RUB/duo"
    files = ["DUO-A1_Kapitel1.txt", "DUO-A1.2.txt", "DUO-B1.txt"]

    for f in files:
        duo_parser = DuoParser(
            duo_path, f, sample_extraction=False,)

        syllables = duo_parser.sentences_set_syllable_length(
            syllable_amount=0, equality="greater"
        )

        duo_parser.save_syllabized_results(syllables)
