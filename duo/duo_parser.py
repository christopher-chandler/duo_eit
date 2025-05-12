import re
import statistics

from collections import Counter

# Pip
import pandas as pd
import spacy
from spacy_syllables import SpacySyllables

# Custom
from duo.duo_getter import DuoFileGetter
from duo.decorators.exec_time import measure_func_exec_time, post_progress

nlp = spacy.load("de_core_news_sm")

nlp.add_pipe("syllables", after="tagger", config={"lang": "de_DE"})


class DuoParser(DuoFileGetter):
    """
    A class to process and analyze a Duo file, extracting and syllabizing sentences.

    Attributes:
        path (str): The path to the directory containing the Duo file.
        user_file (str): The name of the file to process.
        sample_extraction (bool): Whether to extract a sample of the file (default is False).
        sample_size (int): The number of lines to extract if sample_extraction is enabled (default is 20).
        __spacy_sentences (list): Tokenized sentences using spaCy's tokenizer.
        __spacy_syllabized (dict): Syllabized sentences using spaCy.
        save_file (str): The path where the syllabized results will be saved.
    """

    def __init__(self, path, user_file, sample_extraction=False, sample_size=20):
        """
        Initializes the DuoParser object and sets up the pipeline for sentence tokenization and syllabization.

        Args:
            path (str): The directory path containing the Duo file.
            user_file (str): The file name to process.
            sample_extraction (bool, optional): Whether to extract a sample of the file content. Defaults to False.
            sample_size (int, optional): Number of lines to extract if sample_extraction is enabled. Defaults to 20.
        """
        super().__init__(
            path=path,
            user_file=user_file,
            sample_extraction=sample_extraction,
            sample_size=sample_size,
        )
        self.__spacy_sentences = self.spacy_tokenizer()
        self.__spacy_syllabized = self.spacy_syllabizer()
        self.save_file = f"results/{user_file}_syllables.csv"

    @staticmethod
    def __pipeline_step(
        sentences_to_process: list = None,
        regular_expression: re.compile = None,
        expression_operation: str = "find_all",
        replacement_text: str = " ",
        length: int = None,
    ) -> list:
        """
        A helper method for performing various operations on sentences, such as removing or modifying content.

        Args:
            sentences_to_process (list): List of sentences to process.
            regular_expression (re.Pattern): The regular expression pattern to use.
            expression_operation (str): The operation to perform with the regex (`"find_all"` or `"sub"`).
            replacement_text (str): The text to replace matched expressions with if performing `"sub"`.
            length (int, optional): The minimum number of words required in a sentence for it to be kept.

        Returns:
            list: A list of processed sentences.
        """
        sentence_results = list()

        if length is None:
            for sen in sentences_to_process:

                if expression_operation == "find_all":
                    if not regular_expression.findall(sen):
                        sentence_results.append(sen)

                elif expression_operation == "sub":
                    res = re.sub(regular_expression, replacement_text, sen)
                    sentence_results.append(res.strip())
        else:
            for sen in sentences_to_process:
                elements = sen.split()
                if len(elements) > length:
                    sentence_results.append(sen)

        return sentence_results

    @staticmethod
    def __regex(**kwargs) -> dict:
        """
        Generates a set of regular expressions to handle specific sentence cleaning operations.

        Args:
            kwargs: Additional arguments passed to the method, including sentences to strip tab and whitespace.

        Returns:
            dict: A dictionary of compiled regular expressions for sentence cleaning.
        """
        sentences_strip_tab_whitespace = kwargs.get("sentences_strip_tab_whitespace")

        line_tab_break = re.compile("^\t\n$|^\s*\n\s*$")
        tab_whitespace = re.compile("\n|\t")
        invalid_char = re.compile("\uf0a7| |❍|●|-|❏")
        numbers = re.compile("\d")

        sentence_counter = Counter(sentences_strip_tab_whitespace)
        d = {k: v for k, v in sentence_counter.items() if v >= 3}

        headers = re.compile("|".join(d.keys()))

        expressions = {
            "line_tab_break": line_tab_break,
            "headers": headers,
            "invalid_char": invalid_char,
            "tab_whitespace": tab_whitespace,
            "numbers": numbers,
        }

        return expressions

    @measure_func_exec_time
    def sentences_preprocess(self, spacy_sentence_tokenizer: bool = True) -> dict:
        """
        Preprocesses the sentences by tokenizing, removing unwanted characters, and applying regex operations.

        Args:
            spacy_sentence_tokenizer (bool, optional): Whether to use spaCy's sentence tokenizer. Defaults to True.

        Returns:
            dict: A dictionary with various versions of the sentences (raw, no whitespace, set length, etc.).
        """
        duo_file_data = self.get_raw_duo_file_content()
        tokenized_sentences = list()

        if spacy_sentence_tokenizer:
            for sen in duo_file_data:
                doc = nlp(sen)
                for s in doc.sents:
                    tokenized_sentences.append(str(s))
        else:
            tokenized_sentences = duo_file_data

        regex = self.__regex()

        line_tab_break = regex.get("line_tab_break")
        tab_whitespace = regex.get("tab_whitespace")

        sentences_empty_removed = self.__pipeline_step(
            sentences_to_process=tokenized_sentences, regular_expression=line_tab_break
        )
        sentences_set_length = self.__pipeline_step(sentences_empty_removed, length=2)
        sentences_strip_tab_whitespace = self.__pipeline_step(
            sentences_to_process=sentences_set_length,
            regular_expression=tab_whitespace,
            expression_operation="sub",
        )

        regex = self.__regex(
            sentences_strip_tab_whitespace=sentences_strip_tab_whitespace
        )
        headers = regex.get("headers")

        sentence_headers_removed = self.__pipeline_step(
            sentences_to_process=sentences_strip_tab_whitespace,
            regular_expression=headers,
        )
        invalid_char = regex.get("invalid_char")
        sentence_invalid_char_removed = self.__pipeline_step(
            sentences_to_process=sentence_headers_removed,
            regular_expression=invalid_char,
        )
        numbers = regex.get("numbers")
        sentence_numbers_removed = self.__pipeline_step(
            sentences_to_process=sentence_invalid_char_removed,
            regular_expression=numbers,
        )

        processed = sentence_numbers_removed

        sentence_process_results = {
            "raw": duo_file_data,
            "no_white_space": "",
            "set_length": "",
            "no_headers": "",
            "processed": processed,
        }

        return sentence_process_results

    @measure_func_exec_time
    def spacy_tokenizer(self):
        """
        Tokenizes the sentences using spaCy's sentence tokenizer and filters based on POS tags.

        Returns:
            list: A list of tokenized sentences that meet the inclusion/exclusion criteria.
        """
        spacy_sentences = list()

        processed_sentences = self.sentences_preprocess().get("processed")
        docs = [nlp(sentence) for sentence in processed_sentences]

        excluded_tags = {"NUM"}
        include_tags = {"VERB"}

        for sen in docs:
            pos = set()
            for tok in sen:
                pos.add(tok.pos_)

            if not excluded_tags.intersection(pos):
                if include_tags.intersection(pos):
                    spacy_sentences.append(sen)

        return spacy_sentences

    def spacy_syllabizer(self):
        """
        Applies spaCy's syllable parsing to the tokenized sentences and stores syllable information.

        Returns:
            dict: A dictionary mapping sentences to their syllable breakdowns.
        """
        spacy_sentences = self.__spacy_sentences
        results = dict()

        for sentence in spacy_sentences:
            syllables = list()
            for word in sentence:

                if word._.syllables is not None:
                    syllables.append(word._.syllables)
                else:
                    syllables.append("∅")

            results[sentence] = syllables
            syllables = list()

        return results

    @measure_func_exec_time
    def sentences_set_syllable_length(self, syllable_amount=10, equality="greater"):
        """
        Filters sentences based on the number of syllables they contain.

        Args:
            syllable_amount (int, optional): The threshold number of syllables for filtering. Defaults to 10.
            equality (str, optional): Whether to filter for sentences with syllables greater or less than the threshold. Defaults to "greater".

        Returns:
            dict: A dictionary of sentences filtered by syllable length.
        """
        spacy_syllabized = self.__spacy_syllabized

        syllable_results = dict()

        for sen in spacy_syllabized:

            syllables = spacy_syllabized.get(sen)
            f = [x for xs in syllables for x in xs]
            f_len = len(f)

            if equality == "greater":
                if f_len >= syllable_amount:
                    syllable_results[sen] = f_len
            elif equality == "less":
                if f_len <= syllable_amount:
                    syllable_results[sen] = f_len

        sorted_results = dict(
            sorted(syllable_results.items(), key=lambda item: item[1], reverse=True)
        )

        return sorted_results

    @measure_func_exec_time
    def save_syllabized_results(self, syllables) -> None:
        """
        Saves the syllabized results to a CSV file and prints summary statistics.

        Args:
            syllables (dict): A dictionary of sentences and their syllable counts.
        """
        outgoing_file = self.save_file

        df = pd.DataFrame(list(syllables.items()), columns=["Sentence", "Syllables"])
        syllable_value = syllables.values()
        df.index.name = "Num"
        print(df.head())

        mean = statistics.mean(syllable_value)
        mode = statistics.mode(syllable_value)
        stdev = statistics.stdev(syllable_value)
        sen_amount = len(syllables)

        print(
            f"\nSentences: {sen_amount} | Mean: {mean:.2f} | Mode: {mode} | Std Dev:"
            f" {stdev:.2f}"
        )

        df.to_csv(outgoing_file)


if __name__ == "__main__":
    pass
