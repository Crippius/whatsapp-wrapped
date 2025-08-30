"""Utility functions for parsing WhatsApp chat exports and analyzing message data."""

import os
import re
import pandas as pd
import matplotlib.pyplot as plt
from string import punctuation
from collections import Counter
from datetime import date, timedelta
import nltk
from nltk.corpus import stopwords
from emoji import EMOJI_DATA
from math import pi


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
    regexs = {
        "IOS": {
            "normal": r"\[(\d{2}\/\d{2}\/\d{2}), (\d{2}:\d{2}:\d{2})\] (.*?): (.*)$",
            "info": r"\[(\d{2}\/\d{2}\/\d{2}), (\d{2}:\d{2}:\d{2})\] (.*)$",
        },
        "Android": {
            "normal": r"(\d{2}\/\d{2}\/\d{2}), (\d{2}:\d{2}) - (.*?): (.*)$",
            "info": r"(\d{2}\/\d{2}\/\d{2}), (\d{2}:\d{2}) - (.*)$",
        },
    }
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
            else:  # Info message
                date = info.group(1)
                time = info.group(2)
                who = "info"
                message = info.group(3)
                pass
            if device == "Android":
                time += ":00"
            while message.find("‎") != -1:
                message = message[: message.find("‎")] + message[message.find("‎") + 1 :]
            if (
                who != "info"
            ):  # We can avoid adding info messages to dataframe, not used in analysis
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

    translator = str.maketrans("", "", punctuation)
    most_used_words = Counter()

    for message in messages:
        words = (word.translate(translator).lower() for word in message.split())
        valid_words = (
            word
            for word in words
            if word  # Not empty
            and len(word) > 2  # Skip very short words
            and not word.isdigit()  # Skip numbers
            and word not in blacklist
        )  # Not in blacklist

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
    for i in list(in_dict.keys())[: max_values - others]:
        out_dict[i] = in_dict[i]
    if others:
        if len(list(in_dict.keys())[max_values - others :]) == 1:
            out_dict[list(in_dict.keys())[max_values - others]] = in_dict[
                list(in_dict.keys())[max_values - others]
            ]
        else:
            txt = {"en": "Others", "it": "Altri"}
            out_dict[txt[lang]] = sum(
                [i for i in list(in_dict.values())[max_values - others :]]
            )
    return out_dict


def sort_dict(
    in_dict: dict,
    max_values: int = -1,
    reverse: bool = True,
    others: bool = True,
    lang="en",
) -> dict:
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
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
    return os.path.join(project_root, filename)


def get_daily_message_counts(df: pd.DataFrame, interval: str = "day") -> list:
    """Get daily message counts from chat dataframe, matching plot_number_of_messages logic.

    :param df: pandas DataFrame with 'date' column
    :param interval: time interval for grouping messages ("day", "week", "month", "year")
    :return: list of tuples (day, count) sorted by date
    """
    if df.empty:
        return []

    # Match the exact logic from plot_number_of_messages
    x_dict = {
        "day": pd.date_range(df.date.iloc[0], date.today(), freq="D"),
        "week": pd.date_range(
            df.date.iloc[0] - pd.tseries.offsets.Week(1), date.today(), freq="W-MON"
        ),
        "month": pd.date_range(
            df.date.iloc[0] - pd.tseries.offsets.MonthBegin(1), date.today(), freq="MS"
        ),
        "year": pd.date_range(
            df.date.iloc[0] - pd.tseries.offsets.YearBegin(1), date.today(), freq="YS"
        ),
    }

    if interval not in x_dict:
        return []

    x_pos = x_dict[interval]
    daily_counts = []

    for i in x_pos:
        if interval == "day":
            point = len(df[df.date == i])
        elif interval == "week":
            point = len(df[df.date - df.date.dt.weekday * timedelta(days=1) == i])
        elif interval == "month":
            point = len(df[df.date.dt.to_period("M").dt.to_timestamp() == i])
        elif interval == "year":
            point = len(df[df.date.dt.to_period("Y").dt.to_timestamp() == i])
        daily_counts.append((str(i), point))

    return daily_counts


def get_most_used_words(df: pd.DataFrame, max_words: int = 100, who: str = "") -> list:
    """Get most used words from chat messages, matching plot_most_used_words logic.

    :param df: pandas DataFrame with 'message' column
    :param max_words: maximum number of words to return
    :param who: filter words by specific user (default is all users)
    :return: list of tuples (word, count) sorted by frequency
    """
    if df.empty:
        return []

    # Filter messages by user if specified (matching plot_emojis logic)
    messages = (
        df.message
        if who == "" or who not in df.who.unique()
        else df[df.who == who].message
    )

    # Use the exact same logic as plot_most_used_words
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords")

    # Create a set of stopwords from both languages and custom blacklist
    stop_words = set()
    stop_words.update(stopwords.words("english"))
    stop_words.update(stopwords.words("italian"))
    stop_words.update(
        i.strip()
        for i in open(get_data_file_path("lists/blacklist.txt"), "r").readlines()
    )

    most_used_words = get_message_freq_dict(messages, blacklist=list(stop_words))

    # Convert to list of tuples and limit to max_words
    word_list = [(word, count) for word, count in most_used_words.items()]
    word_list.sort(key=lambda x: x[1], reverse=True)
    return word_list[:max_words]


def get_most_used_emojis(df: pd.DataFrame, max_emojis: int = 15, who: str = "") -> list:
    """Get most used emojis from chat messages, matching plot_emojis logic exactly.

    :param df: pandas DataFrame with 'message' column
    :param max_emojis: maximum number of emojis to return
    :param who: filter emojis by specific user (default is all users)
    :return: list of tuples (emoji, count) sorted by frequency
    """
    if df.empty:
        return []

    # Filter messages by user if specified (matching plot_emojis logic)
    messages = (
        df.message
        if who == "" or who not in df.who.unique()
        else df[df.who == who].message
    )

    # Use the exact same logic as plot_emojis
    emojis = {}
    for message in messages:
        for char in message:
            if char in EMOJI_DATA:
                if char not in emojis:
                    emojis[char] = 0
                emojis[char] += 1

    for skin in ["🏻", "🏼"]:
        if skin in emojis:
            emojis.pop(skin)

    # Sort and limit to max_emojis
    emoji_list = [(emoji, count) for emoji, count in emojis.items()]
    emoji_list.sort(key=lambda x: x[1], reverse=True)
    return emoji_list[:max_emojis]


def spider_plot(categories: list, values: list) -> None:
    """Create spider plot.

    :param categories: list of categories (labels)
    :param values: list of values"""
    angles = [n / float(len(categories)) * 2 * pi for n in range(len(categories))]
    angles += angles[:1]
    values += values[:1]
    ax = plt.subplot(111, polar=True)
    plt.xticks(angles[:-1], categories, size=11)
    ax.set_rlabel_position(0)
    first_digit = int(str(max(values))[0])
    if first_digit < 5:
        labels = [
            i * 10 ** (len(str(max(values))) - 1)
            for i in [j for j in (1, 2, 3, 4) if j * 6 / 5 < first_digit]
        ] + [max(values)]
    else:
        labels = [
            i * 10 ** (len(str(max(values))) - 1)
            for i in [j for j in (2, 4, 6, 8) if j * 6 / 5 < first_digit]
        ] + [max(values)]
    plt.yticks(labels, [str(i) for i in labels], color="grey", size=7)
    plt.ylim(0, max(values) * 12 / 10)
    ax.plot(angles, values, linewidth=1, linestyle="solid", color="#128c7f")
    ax.fill(angles, values, alpha=0.5, color="#26d367")


def inverted_barh_plot(y: int, x: int):
    """Invert barh plot (right to left).

    :param y: list of y values
    :param x: list of x values"""

    fig, ax = plt.subplots()
    ax.barh(y, x, align="center", color="#26d367")
    ax.set_yticks([])
    ax.set_yticklabels([])
    ax.invert_yaxis()
    ax.invert_xaxis()
    ax2 = ax.twinx()
    ax2.set_ylim(ax.get_ylim())
    ax2.set_yticks(y)


def add_labels_to_bar(
    plot,
    labels: list,
    font_size: int = 18,
    dir: str = "vertical",
    pos: str = "external",
) -> None:
    """Add auxiliary labels near the sides of the bars.

    :param plot: bar plot object
    :param labels: list of labels to add
    :param font_size: font size of the labels
    :param dir: "vertical" or "horizontal"
    :param pos: "external" or "internal" (only for horizontal)"""

    if dir == "vertical":
        plt.ylim(0, plt.ylim()[1] + plt.ylim()[1] / 10)
        maxi = max([rect1.get_height() for rect1 in plot])
        for rect1, label in zip(plot, labels):
            plt.annotate(
                label,
                (
                    rect1.get_x() + rect1.get_width() / 2,
                    rect1.get_height() + maxi / 100,
                ),
                ha="center",
                va="bottom",
                fontsize=font_size,
            )
    else:
        plt.xlim(0, plt.xlim()[1] + plt.xlim()[1] / 10)
        maxi = max([rect1.get_y() for rect1 in plot])
        for rect1, label in zip(plot, labels):
            if pos == "external":
                x = rect1.get_y() + rect1.get_width() + maxi / 100
                ha = "right"
            else:
                x = plt.xlim()[1] / 50
                ha = "left"
            plt.annotate(
                label,
                (x, rect1.get_y()),
                ha=ha,
                va="bottom",
                fontsize=font_size,
            )
    return
