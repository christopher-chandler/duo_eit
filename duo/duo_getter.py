import os


class DuoFileGetter:
    """
    A class to retrieve and manage files from a specified directory path.

    Attributes:
        path (str): The directory path to search for files.
        user_file (str): The specific file name to retrieve from the directory.
        _file_data (dict): A dictionary of files and their absolute paths.
        sample_extraction (bool): Flag to determine whether to extract a sample of the file content.
        sample_size (int): The number of lines to extract if sample_extraction is enabled.
    """

    def __init__(
        self,
        path: str,
        user_file: str,
        sample_extraction: bool = False,
        sample_size: int = 20,
    ):
        """
        Initializes the DuoFileGetter object with given parameters.

        Args:
            path (str): The directory path to search for files.
            user_file (str): The specific file name to retrieve from the directory.
            sample_extraction (bool, optional): Flag to enable sample extraction. Defaults to False.
            sample_size (int, optional): The number of lines to extract as a sample. Defaults to 20.
        """
        self.path = path
        self.user_file = user_file
        self._file_data = self.get_duo_abs_file_path()
        self.sample_extraction = sample_extraction
        self.sample_size = sample_size

    def __repr__(self) -> str:
        """
        Returns a string representation of the object, including a preview of the file content.

        Returns:
            str: A string summarizing the file's name, content length, and a preview of the first few lines.
        """
        file_content = self.get_raw_duo_file_content()
        content_length = len(file_content)
        preview = file_content[:5]

        return (
            f"The file '{self.user_file}' contains {content_length} lines."
            f"\nPreview: {preview}..."
        )

    def get_duo_abs_file_path(self) -> dict:
        """
        Retrieves the absolute paths of all files in the specified directory.

        Returns:
            dict: A dictionary mapping file names to their absolute paths.
        """
        dir_files = dict()
        for root, _, files in os.walk(self.path):
            for f in files:
                dir_files[f] = os.path.join(root, f)
        return dir_files

    def get_raw_duo_file_content(self) -> list:
        """
        Retrieves the content of the user-specified file.

        If sample_extraction is enabled, only the first 'sample_size' lines are returned.

        Returns:
            list: A list of strings representing the lines in the file.
        """
        file_data = self._file_data
        user_file = self.user_file

        user_choice_file = file_data.get(user_file)

        with open(user_choice_file, mode="r", encoding="utf-8") as incoming_file:
            if self.sample_extraction:
                return incoming_file.readlines()[: self.sample_size]
            else:
                return incoming_file.readlines()


if __name__ == "__main__":
    duo_path = "/Users/christopherchandler/code_repos/RUB/duo"

    duo_files = DuoFileGetter(duo_path, "DUO-A1.2.txt")
    print(duo_files)
