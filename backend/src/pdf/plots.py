"""
Plotting functions for WhatsApp Wrapped PDF generation.
"""

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.font_manager import FontProperties
from matplotlib import rcParams, font_manager

import os
import pandas as pd
from wordcloud import WordCloud
from datetime import date, timedelta

from src.utils import *

class Plotter:
    """Class for creating and saving WhatsApp Wrapped plots with common parameters."""
    
    def __init__(self, df: pd.DataFrame, output_path: str, lang: str = "en"):
        """Initialize Plotter with common parameters.
        
        :param df: DataFrame containing chat data
        :param output_path: path to save the plots
        :param lang: language for titles and labels ("en" or "it")
        """
        self.df = df
        self.output_path = output_path
        self.lang = lang
        self.counter = 0
    
    def update_counter(self) -> None:
        """Increment the counter for naming output files."""
        self.counter += 1
    
    def save_image(self, filename: str = None) -> None:
        """Save the current plot to output_path with counter-based naming.
        
        :param filename: optional custom filename (without extension)
        """
        if filename is None:
            filename = f"{self.counter}.png"
        else:
            filename = f"{self.counter}_{filename}.png"
        
        plt.savefig(os.path.join(self.output_path, filename), transparent=True)
        plt.close()
    
    def plot_emojis(self, who: str = "", reverse: bool = False, info: bool = True) -> None:
        """Plot most used emojis in chat and save to output_path.
        
        :param who: filter emojis by specific user (default is all users)
        :param reverse: reverse the order of the bars (default is False)
        :param info: whether to display total number of emojis used (default is True)
        """
        
        font_path = get_data_file_path('my_fonts/seguiemj.ttf')
        try:
            font_manager.fontManager.addfont(font_path)
        except Exception:
            pass
        prop = FontProperties(fname=font_path)
        rcParams['font.family'] = prop.get_name()
        
        emoji_data = get_most_used_emojis(self.df, max_emojis=7, who=who)
        emojis = {emoji: count for emoji, count in emoji_data}
        emojis = sort_dict(emojis, 7, reverse=reverse, others=False, lang=self.lang)
        if len(emojis.keys()) == 0:
            emojis["🏼"] = 0
        
        title = {"en": "Most used Emojis:", "it": "Emoji più utilizzate:"}
        fig, ax = plt.subplots()
        ax.set_title(title[self.lang])
        plot = ax.bar(emojis.keys(), emojis.values(), color="#26d367")
        ax.set_xticks(range(len(emojis)))
        ax.set_xticklabels(list(emojis.keys()))
        for tick in ax.get_xticklabels():
            if prop is not None:
                tick.set_fontproperties(prop)
            tick.set_fontsize(20)
        if info:
            txt = {"en": f"{sum(emojis.values())} total\nemojis 😯", "it": f"{sum(emojis.values())} emoji\ntotali 😯"}
            axlim = ax.get_xlim()
            ayl = ax.get_ylim()
            ax.text(x=axlim[0]+1 if reverse else axlim[1]-1, y=ayl[1]*9/10, s=txt[self.lang],
                    ha="left" if reverse else "right", va="top", fontsize=16,
                    bbox=dict(facecolor='none', edgecolor='black', boxstyle='round,pad=1'),
                    fontproperties=prop if prop is not None else None)
        emojis_to_size_dict = {1:28, 2:26, 3:24, 4:22, 5:21, 6:20, 7:18, 8:16, 9:14, 10:12}
        add_labels_to_bar(plot, emojis.values(), font_size=emojis_to_size_dict[len(emojis)], dir="vertical")
        self.save_image()
    
    def plot_number_of_messages(self, interval: str = "day") -> None:
        """Plot number of messages per interval and save to output_path.
        
        :param interval: time interval for grouping messages ("day", "week", "month", "year")
        """

        daily_counts = get_daily_message_counts(self.df, interval=interval)
        if not daily_counts:
            return
        x_pos = [pd.to_datetime(day) for day, _ in daily_counts]
        y_pos = [count for _, count in daily_counts]
        
        running_average = []
        window = []
        
        for i, point in enumerate(y_pos):
            if len(window) == 0:
                window = [point*(5)**(-1)]*5
            window.pop(0)
            window.append(point)
            running_average.append((sum(window)) / 5)
        
        plt.plot(x_pos, y_pos, color="#26d367")
        diff = pd.to_datetime(date.today())-self.df.date.iloc[0]
        if ((interval == "month" and diff > timedelta(days=360)) or
            (interval == "week" and diff > timedelta(days=180)) or
            (interval == "day" and diff > timedelta(days=30))):
            plt.plot(x_pos, running_average, color="#075e55")
            if pd.to_datetime(x_pos[-1])-pd.to_datetime(x_pos[0]) < timedelta(days=365):
                if pd.to_datetime(x_pos[-1])-pd.to_datetime(x_pos[0]) < timedelta(days=365//2):
                    plt.gca().xaxis.set_major_formatter(DateFormatter('%d-%m'))
                else:
                    plt.gca().xaxis.set_major_formatter(DateFormatter('%m-%y'))
        
        plt.grid(axis="y")
        interval_dict = {"day": {"en": "day", "it": "giorno"}, "week": {"en": "week", "it": "settimana"},
                        "month": {"en": "month", "it": "mese"}, "year": {"en": "year", "it": "anno"}}
        title = {"en": f"Number of messages per {interval_dict[interval][self.lang]}",
                 "it": f"Numero di messaggi per {interval_dict[interval][self.lang]}"}
        plt.title(title[self.lang])
        self.save_image()

    def plot_day_of_the_week(self) -> None:
        """Plot number of messages sent per weekday and save to output_path."""

        weekday = {"en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                   "it": ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]}
        y_pos = [len(self.df[self.df.date.dt.day_name() == i]) for i in weekday["en"]]
        spider_plot(weekday[self.lang], y_pos)
        title = {"en": "Number of messages per weekday:",
                 "it": "Numero di messaggi per giorno della settimana:"}
        plt.title(title[self.lang], pad=30)
        self.save_image()

    def plot_most_used_words(self, wordcloud: bool = True) -> None:
        """Plot most used words as barplot or wordcloud and save to output_path.
        
        :param wordcloud: whether to plot a wordcloud (True) or barplot (False)
        """
        
        most_used_words_data = get_most_used_words(self.df, max_words=100)    
        most_used_words = {word: count for word, count in most_used_words_data}
        
        if wordcloud:
            plot = WordCloud(width=400, height=300, max_words=100, stopwords=stopwords, min_font_size=6,
                             background_color=None, mode="RGBA", colormap="summer").generate_from_frequencies(most_used_words)
            plt.imshow(plot, interpolation="bilinear")
            plt.axis("on")
            plt.xticks([])
            plt.yticks([])
        else:
            plt.bar(list(most_used_words.keys()), most_used_words.values(), color="#26d367")

        title = {"en": "Most used words:", "it": "Parole più utilizzate:"}
        plt.title(title[self.lang])
        self.save_image()

    def plot_most_active_people(self, group: bool = True, name: str = None) -> None:
        """Plot most number of messages sent per person and save to output_path.
        
        :param group: whether to plot a grouped barh (True) or pie chart (False)
        :param name: name of the group (if group is True)
        """
        people = {font_friendly(k): len(self.df[self.df.who == k]) for k in set(self.df.who)}
        if "info" in people.keys():
            people.pop("info")
        people = sort_dict(people, 7, reverse=True, lang=self.lang)
        if group:
            title = {"en": f"Most active people in {name}", "it": f"Persone più attive in {name}:"}
            plt.title(title[self.lang])
            set_to_font_size = {1: 150, 2: 45, 3: 40, 4: 35, 5: 32, 6: 25, 7: 21, 8: 18, 9: 15, 10: 14}
            plot = plt.barh([str(i) for i in people.values()], people.values(), color="#26d367")
            add_labels_to_bar(plot, people.keys(), font_size=set_to_font_size[len(people)], dir="horizontal", pos="internal")
        else:
            title = {"en": "Number of messages:", "it": "Numero di messaggi inviati:"}
            plt.title(title[self.lang])
            plt.pie(x=people.values(), labels=people.keys(), colors=("#26d367", "#128c7f"), textprops={"fontsize": 14},
                    autopct=lambda x: f"{int(round((x/100)*sum(people.values()), 0))} messaggi\n({round(x, 2)}%)")
        self.save_image()

    def plot_time_of_messages(self) -> None:
        """Plot number of messages per time period and save to output_path."""

        title = {"en": "Number of messages per time of day:",
                 "it": "Numero di messaggio per periodo del giorno:"}
        plt.title(title[self.lang])
        x_pos = [timedelta(hours=i//2, minutes=30*(i%2)) for i in range(0, 48)]
        x_pos = x_pos[6:] + x_pos[:6]
        slotted_times = [i.floor("30min") for i in self.df.time]
        y_pos = [slotted_times.count(i) for i in x_pos]
        x_pos_fmt = [f"{'0' if i < timedelta(hours=10) else ''}{str(i)[:-3]}" for i in x_pos]
        plt.plot_date(x_pos_fmt, y_pos, color="#128c7f")
        plt.grid(axis="y")
        plt.fill_between(x_pos_fmt, y_pos, color="#26d367")
        N = 6
        x_pos_fmt = [x_pos_fmt[i] if not i % N else "" for i in range(len(x_pos_fmt))]
        plt.xticks(x_pos_fmt)
        self.save_image() 

