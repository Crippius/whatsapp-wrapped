"""
Data extraction and cleaning functions for WhatsApp Wrapped.
"""

import re
import pandas as pd
from string import punctuation
from datetime import timedelta
from collections import Counter


def IOS_or_Android(txt: str, regexs: dict) -> str:
    """Return from which device the file is from (Android or iPhone) by checking the text to some regexs."""
    for regex in regexs["IOS"].values():
        if re.search(regex, txt) is not None:
            return "IOS"
    for regex in regexs["Android"].values():
        if re.search(regex, txt) is not None:
            return "Android"
    return "IDK"


def get_data(file: str, font_friendly=None) -> list:
    """Extract the info inside the .txt file."""
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


def remove_header(df: pd.DataFrame) -> pd.DataFrame:
    """Remove the first messages if header is present (to be updated)."""
    return df[3:].reset_index() if len(df) > 3 else df


def get_message_freq_dict(messages: pd.Series, blacklist: list = []) -> dict:
    """Create dict with frequency of words."""
    # blacklist = map(str.lower, blacklist)
    
    translator = str.maketrans('', '', punctuation)
    
    most_used_words = Counter()
    
    for message in messages:
        words = (word.translate(translator).lower() 
                for word in message.split())
        valid_words = (word for word in words 
                      if word                           # Not empty
                      and len(word) > 2                 # Skip very short words
                      and not word.isdigit()           # Skip numbers
                      and word not in blacklist)   # Not in blacklist
        
        most_used_words.update(valid_words)
    
    return dict(most_used_words)


def concentrate_values(in_dict: dict, max_values: int, others: bool, lang="en") -> dict:
    """Make dictionary smaller by removing keys with smaller values."""
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
    """Sort dict by values and optionally concentrate keys."""
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
    """Return the maximum value and the index in which it is placed."""
    best = float("-inf")
    best_index = -1
    for i in range(len(lst)):
        if type(lst[i]) != int:
            continue
        if lst[i] > best:
            best = lst[i]
            best_index = i
    return best, best_index 