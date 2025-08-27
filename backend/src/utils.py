"""Utility functions for parsing WhatsApp chat exports and analyzing message data."""

import os
import re
import pandas as pd
from string import punctuation
from collections import Counter


def IOS_or_Android(txt: str, regexs: dict) -> str:
    """Return from which device the file is from (Android or iPhone) by checking the text to some regexs.
    
    :param txt: text to check
    :param regexs: dictionary with regexs to check
    :return: "IOS" if iPhone, "Android" if Android, "IDK" if not recognized
    """
    for regex in regexs["IOS"].values():
        if re.search(regex, txt) is not None:
            return "IOS"
    for regex in regexs["Android"].values():
        if re.search(regex, txt) is not None:
            return "Android"
    return "IDK"


def get_data(file: str) -> list:
    """Extract the info inside the .txt file.
    
    :param file: path to the .txt file
    :return: list of lists with date, time, who, message"""
    try:
        fp = open(file, "r", encoding="utf8")
    except UnicodeDecodeError:
        fp = open(file, "r", encoding="latin1")
    data = []
    trame = fp.readline()
    regexs = {"IOS": {"normal": r"\[(\d{2}\/\d{2}\/\d{2}), (\d{2}:\d{2}:\d{2})\] (.*?): (.*)$",
                      "info": r"\[(\d{2}\/\d{2}\/\d{2}), (\d{2}:\d{2}:\d{2})\] (.*)$"},
              "Android": {"normal": r"(\d{2}\/\d{2}\/\d{2}), (\d{2}:\d{2}) - (.*?): (.*)$",
                          "info": r"(\d{2}\/\d{2}\/\d{2}), (\d{2}:\d{2}) - (.*)$"}}
    device = IOS_or_Android(trame, regexs)
    while trame != "":
        norm = re.search(regexs[device]["normal"], trame)
        info = re.search(regexs[device]["info"], trame)
        if norm is not None or info is not None:
            if norm is not None:
                date = norm.group(1)
                time = norm.group(2)
                who = font_friendly(norm.group(3)) if font_friendly else norm.group(3)
                message = norm.group(4)
            else: # Info message
                date = info.group(1)
                time = info.group(2)
                who = "info"
                message = info.group(3)
                pass
            if device == "Android":
                time += ":00"
            while message.find("‎") != -1:
                message = message[:message.find("‎")] + message[message.find("‎") + 1:]
            if who != "info": # We can avoid adding info messages to dataframe, not used in analysis
                data.append([date, time, who, message])
        elif len(data) != 0:
            data[-1][3] += "\n" + trame
        trame = fp.readline()
    return data



def get_message_freq_dict(messages: pd.Series, blacklist: list = []) -> dict:
    """Create dict with frequency of words.
    
    :param messages: pandas Series with messages
    :param blacklist: list of words to ignore
    :return: dictionary with words as keys and frequency as values"""
    # blacklist = map(str.lower, blacklist)
    
    translator = str.maketrans('', '', punctuation)
    most_used_words = Counter()
    
    for message in messages:
        words = (word.translate(translator).lower() 
                for word in message.split())
        valid_words = (word for word in words 
                      if word                      # Not empty
                      and len(word) > 2            # Skip very short words
                      and not word.isdigit()       # Skip numbers
                      and word not in blacklist)   # Not in blacklist
        
        most_used_words.update(valid_words)
    
    return dict(most_used_words)


def concentrate_values(in_dict: dict, max_values: int, others: bool, lang="en") -> dict:
    """Make dictionary smaller by removing keys with smaller values.
    
    :param in_dict: input dictionary
    :param max_values: maximum number of keys to keep
    :param others: whether to group smaller keys into "Others
    :param lang: language for "Others" key ("en" or "it")
    :return: concentrated dictionary"""

    if len(in_dict.keys()) <= max_values:
        return in_dict
    out_dict = {}
    for i in list(in_dict.keys())[:max_values - others]:
        out_dict[i] = in_dict[i]
    if others:
        if len(list(in_dict.keys())[max_values - others:]) == 1:
            out_dict[list(in_dict.keys())[max_values - others]] = in_dict[list(in_dict.keys())[max_values - others]]
        else:
            txt = {"en": "Others", "it": "Altri"}
            out_dict[txt[lang]] = sum([i for i in list(in_dict.values())[max_values - others:]])
    return out_dict


def sort_dict(in_dict: dict, max_values: int = -1, reverse: bool = True, others: bool = True, lang="en") -> dict:
    """Sort dict by values and optionally concentrate keys.
    
    :param in_dict: input dictionary
    :param max_values: maximum number of keys to keep (-1 to keep all)
    :param reverse: whether to reverse the order (True for descending)
    :param others: whether to group smaller keys into "Others"
    :param lang: language for "Others" key ("en" or "it")
    :return: sorted (and possibly concentrated) dictionary"""


    out_dict = {}
    sorted_keys = sorted(in_dict, key=in_dict.get, reverse=True)
    for w in sorted_keys:
        out_dict[w] = in_dict[w]
    if max_values != -1:
        out_dict = concentrate_values(out_dict, max_values, others, lang)
    if reverse:
        out_dict = {k: out_dict[k] for k in list(out_dict.keys())[::-1]}
    return out_dict


def max_and_index(lst: list) -> tuple:
    """Return the maximum value and the index in which it is placed.
    
    :param lst: input list
    :return: tuple with maximum value and index"""
    
    best = float("-inf")
    best_index = -1
    for i in range(len(lst)):
        if type(lst[i]) != int:
            continue
        if lst[i] > best:
            best = lst[i]
            best_index = i
    return best, best_index 
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