import string
import os

def font_friendly(txt: str) -> str:
    """Remove bad emojis that make the PDF look bad."""
    bad_emojis = ["️", "⃣", "🏽", "🏼", "🏾", "🏻", "🏿"]
    new_txt = ""
    for i in txt:
        if i not in bad_emojis:
            new_txt += i
    return new_txt


def check_text(txt: str, char_per_line: int = 50) -> str:
    """Check how big the message bubble needs to be (one, two, three lines)."""
    bubble = 1
    counter = 0
    for i in txt:
        if counter == char_per_line - 1 or i == "\n":
            bubble += 1
            if bubble == 3:
                break
            counter = -1
        counter += 1
    bubble_dict = {1: "one", 2: "two", 3: "three"}
    return bubble_dict[bubble]


def transform_text(txt: str, char_per_line: int = 50) -> str:
    """Transform string of text to fit into message bubble."""
    new_txt = ""
    counter = 0
    times = 0
    for i in txt:
        if counter == char_per_line or i == "\n":
            counter = -1
            times += 1
            if times == 3:
                break
            new_txt += "\n"
        if i != "\n":
            new_txt += i
        counter += 1
    return new_txt 


def get_data_file_path(filename):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    return os.path.join(project_root, filename)