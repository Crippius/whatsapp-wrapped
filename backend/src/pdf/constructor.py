"""
PDF construction logic for WhatsApp Wrapped.
"""


import re
import pandas as pd
from fpdf import FPDF
from datetime import date, timedelta
from os import path, getenv, makedirs, remove

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib import rcParams

from src.utils import * 
from src.pdf.plots import Plotter

# PDF dimensions and layout constants
HEIGHT = 297
WIDTH = 210
GREEN_POS = 108
WHITE_POS = 8
LEFT_PLOT = 5
RIGHT_PLOT = 5 + WIDTH / 2
PLOT_HEIGHT = 75
CHAR_PER_LINE = 50

BASE_DIR = path.dirname(path.abspath(__file__))

# Configure paths based on environment
if getenv('RENDER') == '1':
    INPUT = '/tmp/text_files/'
    OUTPUT = '/tmp/pdfs/'
else:
    INPUT = path.abspath(path.join(BASE_DIR, '../../../text_files/'))
    OUTPUT = path.abspath(path.join(BASE_DIR, '../../../pdfs/'))

makedirs(INPUT, exist_ok=True)
makedirs(OUTPUT, exist_ok=True)


class PDF_Constructor(FPDF):
    """Class to construct the PDF with all the plots and messages."""

    img_path = path.join(BASE_DIR, '../../static/')

    def __init__(self, file: str, lang: str = "en") -> None:
        """Initialize the PDF constructor.
        
        :param file: path to the WhatsApp chat text file
        :param lang: language of the PDF ("en" or "it")"""
        
        # Prepare the file
        if not path.exists(file):
            print("No such file exists")
            self.ok = 0
        else:
            self.ok = 1
        m = re.search("Chat WhatsApp con (.+?).txt", file)
        if m is not None:
            self.name = font_friendly(m.group(1))
        else:
            m = re.search("Chat_WhatsApp_con_(.+?).txt", file)
            if m is not None:
                self.name = font_friendly(m.group(1))
            else:
                self.name = ""

        # Initialize the PDF constructor
        FPDF.__init__(self)
        self.counter = 0
        self.lang = lang

        # Prepare the dataframe
        self.df = pd.DataFrame(get_data(file), columns=["date", "time", "who", "message"])
        self.df.date = pd.to_datetime(self.df.date, format="%d/%m/%y")
        self.df.time = pd.to_timedelta(self.df.time)
        self.group = True
        if len(set(self.df.who)) == 3 and "info" in set(self.df.who):
            self.group = False
            lst = list(set(self.df.who))
            lst.remove("info")
            self.name = tuple([lst[lst.index(self.name)], lst[not lst.index(self.name)]])

        # PDF_Constructor attributes
        self.plot_pos = {"left": LEFT_PLOT, "right": RIGHT_PLOT}
        self.pos = {"left": 0, "right": 0}
        self.last = {"left": None, "right": None}
        self.load = (self.pos["left"] / HEIGHT * self.pos["right"] / HEIGHT) * 100

        # Plotter
        self.plotter = Plotter(self.df, OUTPUT, lang)
        
        # Set the font
        prop = FontProperties(fname=get_data_file_path('my_fonts/seguiemj.ttf'))
        rcParams['font.family'] = prop.get_name()
        self.add_font('seguiemj', '', get_data_file_path('my_fonts/seguiemj.ttf'), uni=True)
        self.set_font('seguiemj', '', 16)
        self.add_structure()

    def add_structure(self) -> None:
        """Add the basic structure of the PDF."""

        self.add_page()
        self.image(path.join(PDF_Constructor.img_path, 'background.png'), x=0, y=0, w=WIDTH, h=HEIGHT)
        self.image(path.join(PDF_Constructor.img_path, 'top_level.png'), x=0, y=0, w=WIDTH)
        self.cell(15, 0, "")
        self.set_text_color(255, 255, 255)
        if self.group:
            txt = {"en": f"Analysis of {self.name} chat", "it": f"Analisi della chat {self.name}"}
            self.multi_cell(WIDTH-70, 0, transform_text(txt[self.lang]))
        else:
            txt = {"en": f"Analysis of {self.name[0]} and {self.name[1]} chat"[:CHAR_PER_LINE],
                   "it": f"Analisi della chat tra {self.name[0]} e {self.name[1]}"[:CHAR_PER_LINE]}
            self.multi_cell(WIDTH-70, 0, txt[self.lang])
        self.set_text_color(0, 0, 0)
        x, y = self.get_x(), self.get_y()
        self.set_auto_page_break(False)
        self.set_y(-20)
        self.image(path.join(PDF_Constructor.img_path, "writing_box.png"), x=20, y=self.get_y()-4, w=WIDTH-40)
        self.cell(30, 0)
        self.set_font_size(12)
        website_url = getenv('WEBSITE_URL', 'https://whatsapp-wrapped.vercel.app')
        txt = {"en": f"Do you want to create your own wrapped? 🤨\nThen try it @ {website_url} 👈",
               "it": f"Vuoi creare il wrapped di una tua chat? 🤨\nVai su {website_url} 👈"}
        self.multi_cell(0, 5, txt[self.lang], align="L")
        self.cell(0, 5, link=website_url)
        self.set_xy(x, y)

    def update_counter(self) -> None:
        """Update the image counter."""
        self.counter += 1
        self.plotter.update_counter()

    def add_image(self, x: int, y: int) -> None:
        """Add an image to the PDF.
        
        :param x: x position
        :param y: y position"""
        self.image(path.join(OUTPUT, f"{self.counter}.png"), x=x, y=y, w=WIDTH/2 - 5, h=PLOT_HEIGHT)

    def prep(self, plot: bool = True) -> bool:
        """Prepare the PDF for adding new content.
        
        :param plot: whether we are adding a plot or a message
        :return: whether the PDF is ready for new content"""
        if self.ok:
            if plot:
                self.update_counter()
                plt.close()
            return True
        else:
            return False

    def update_y(self, pos: str, obj: str, lines: str = "one") -> int:
        """Update the y position for the next object.
        
        :param pos: "left" or "right" position on the PDF
        :param obj: "message" or "plot"
        :param lines: if obj is "message", how many lines the message bubble has ("one", "two" or "three")
        :return: the new y position"""
        
        mess_dict = {"one": 12, "two": 20, "three": 25}
        obj_dict = {(None, "message"): 30, (None, "plot"): 20,
                    ("plot", "message"): 80, ("plot", "plot"): 75,
                    ("message", "message"): mess_dict[lines]+5, ("message", "plot"): mess_dict[lines]+5}
        self.pos[pos] += obj_dict[(self.last[pos], obj)]
        self.last[pos] = obj
        other = "left" if pos == "right" else "right"
        tmp = 100*(((self.pos[pos]+obj_dict[(None, obj)])/HEIGHT)+(self.pos[other]/HEIGHT))
        self.load = tmp if tmp < 100 else 99
        return self.pos[pos]


    def add_emoji_plot(self, pos: str, who: str = "", reverse: bool = False, info: bool = True) -> None:
        """Add the emoji usage plot to the PDF.
        
        :param pos: "left" or "right" position on the PDF
        :param who: name of the person to plot (empty for all)
        :param reverse: whether to reverse the order of the emojis
        :param info: whether to add the info about the plot"""

        if not self.prep():
            return
        self.plotter.plot_emojis(who=who, reverse=reverse, info=info)
        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))


    def add_number_of_messages_plot(self, pos: str, interval: str = "day") -> None:
        """Add the number of messages plot to the PDF.
        
        :param pos: "left" or "right" position on the PDF
        :param interval: interval for the plot ("day", "week", "month", "year")"""

        if not self.prep():
            return
        self.plotter.plot_number_of_messages(interval=interval)
        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))


    def add_day_of_the_week_plot(self, pos:str):
        """Add the day of the week plot to the PDF.
        
        :param pos: "left" or "right" position on the PDF"""

        if not self.prep():
            return
        self.plotter.plot_day_of_the_week()
        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))

    def add_most_used_words_plot(self, pos:str, wordcloud: bool = True) -> None:
        """Add the most used words plot to the PDF.
        
        :param pos: "left" or "right" position on the PDF
        :param wordcloud: whether to use a wordcloud or a bar plot"""
        if not self.prep():
            return
        self.plotter.plot_most_used_words(wordcloud=wordcloud)
        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))

    def add_most_active_people_plot(self, pos:str) -> None:
        """Add the most active people plot to the PDF.
        
        :param pos: "left" or "right" position on the PDF"""

        if not self.prep():
            return
        self.plotter.plot_most_active_people(self.group, self.name)
        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))

    def add_time_of_messages_plot(self, pos:str) -> None:
        """Add the time of messages plot to the PDF.
        
        :param pos: "left" or "right" position on the PDF"""

        if not self.prep():
            return
        self.plotter.plot_time_of_messages()
        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))

    def add_message(self, cat: str, pos: str) -> None:
        """Add a message bubble to the PDF.
        Possible categories are:
        - message_count
        - active_days
        - messages_per_day
        - file_count
        - most_active_day
        - most_active_year
        - most_active_month
        - most_active_weekday
        - most_active_person
        - longest_active_streak
        - longest_inactive_streak
        - first_texter
        - avg_response_time
        - swear_count
        - avg_message_length

        :param cat: category of the message to add
        :param pos: "left" or "right" position on the PDF"""

        if not self.prep(plot=False):
            return
        
        def message_count(self):
            num = len(self.df) if len(self.df) < 39900 else '40000+'
            txt = {"en": f"{num} messages have been sent!\nYou chat so much 🤩",
                   "it": f"Sono stati mandati {num} messaggi!\nVi scrivete un botto! 🤩"}
            return txt[self.lang]
        def active_days(self):
            total = len(set(self.df.date))
            txt = {"en": f"This group has benn active in {total} different days! 🧐",
                   "it": f"Vi siete scritti in {total} giorni diversi! 🧐"}
            return txt[self.lang]
        def messages_per_day(self):
            message_ratio = len(self.df)/len(pd.date_range(self.df.date[0], date.today()))
            message_ratio = round(message_ratio, 2)
            txt = {"en": f"You usually send {message_ratio} messages every day 📱",
                   "it": f"In media vi mandate {message_ratio} messaggi al giorno 📱"}
            return txt[self.lang]
        def file_count(self):
            files = len(self.df[self.df.message == '<Media omessi>'])
            txt = {"en": f"{files} files have been sent in this chatroom!",
                   "it": f"Sono stati inviati {files} file!"}
            return txt[self.lang]
        def most_active_day(self):
            num = max([len(self.df[self.df.date == i]) for i in set(self.df.date)])
            day = max(set(self.df.date), key=lambda d: len(self.df[self.df.date == d])).strftime('%d/%m/%y')
            txt = {"en": f"The most active day has been {day}\n{num} total messages, incredible 🤯",
                   "it": f"Il giorno più attivo è stato il {day}\n{num} messaggi in totale, che giornata 🤯"}
            return txt[self.lang]
        def most_active_year(self):
            lst = [len(self.df[self.df.date.dt.year == i]) for i in set(self.df.date.dt.year)]
            best, year = max_and_index(lst)
            year = list(set(self.df.date.dt.year))[year]
            txt = {"en": f"Most active year: {year} ({best} messaggi)\nThere were some great memories 💭",
                   "it": f"Anno più attivo: {year} ({best} messaggi)\nChe memorie 💭"}
            return txt[self.lang]
        def most_active_month(self):
            lst = [len(self.df[self.df.date.dt.to_period('M').dt.to_timestamp() == i]) for i in set(self.df.date.dt.to_period('M').dt.to_timestamp())]
            best, month = max_and_index(lst)
            month = list(set(self.df.date.dt.to_period('M').dt.to_timestamp()))[month].strftime('%m/%y')
            txt = {"en": f"Most active month: 👇\n{month} ({best} messaggi)",
                   "it": f"Mese più attivo: 👇\n{month} ({best} messaggi)"}
            return txt[self.lang]
        def most_active_weekday(self):
            lst = [len(self.df[self.df.date.dt.day_name() == i]) for i in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]]
            best, weekday = max_and_index(lst)
            txt = {"en": f'Most active weekday: {["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"][weekday]} ({best} messaggi)',
                   "it": f'Giorno più attivo: {["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"][weekday]} ({best} messaggi)'}
            return txt[self.lang]
        def most_active_person(self):
            people = {k: len(self.df[self.df.who == k]) for k in set(self.df.who)}
            person, total = list(sort_dict(people, 1, others=False).items())[0]
            percent = 100*round(total/len(self.df), 2)
            person = font_friendly(person)
            txt = {"en": f"{person} is the most active person!\n They wrote {total} messages ({percent}% of the total) 🤙",
                   "it": f"{person} è la persona più attiva!\n Ha scritto {total} messaggi ({percent}% del totale) 🤙"}
            return txt[self.lang]
        def longest_active_streak(self):
            dates = sorted(list(set(self.df.date)))
            start = dates[0]
            end = dates[0]
            best_streak = 0
            curr_streak = 0
            for i in range(1, len(dates)):
                if dates[i]-dates[i-1] != timedelta(days=1):
                    if curr_streak > best_streak:
                        best_streak = curr_streak
                        start = dates[i-1-curr_streak]
                        end = dates[i-1]
                    curr_streak = 0
                else:
                    curr_streak += 1
            start, end = start.strftime('%d/%m/%y'), end.strftime('%d/%m/%y')
            txt = {"en": f"Longest active streak: {best_streak} days\nFrom {start} to {end} ❤️",
                   "it": f"Streak di giorni attivi più lunga: {best_streak} giorni\nDal {start} al {end} ❤️"}
            return txt[self.lang]
        def longest_inactive_streak(self):
            dates = sorted(list(set(self.df.date)))
            start = "01/01/1900"
            end = "01/01/1900"
            best_streak = timedelta(days=1)
            for i in range(1, len(dates)):
                if dates[i]-dates[i-1] > best_streak:
                    start = dates[i-1]
                    end = dates[i]
                    best_streak = dates[i]-dates[i-1]
            start, end, best_streak = start.strftime('%d/%m/%y'), end.strftime('%d/%m/%y'), best_streak.days
            txt = {"en": f"Longest inactive streak: {best_streak} days\nFrom {start} to {end} ☠️",
                   "it": f"Streak di giorni inattivi più lunga: {best_streak} giorni\nDal {start} al {end} ☠️"}
            return txt[self.lang]
        def first_texter(self):
            people = {}
            for i in range(1, len(self.df)):
                if self.df.date[i] != self.df.date[i-1]:
                    who = self.df.who[i]
                    if who not in people:
                        people[who] = 0
                    people[who] += 1
            people = sort_dict(people, 1, others=False, lang=self.lang)
            person = font_friendly(list(people.keys())[0])
            txt = {"en": f"It's usually {person} who writes first... 🥇",
                   "it": f"Solitamente è {person} che scrive per prim*... 🥇"}
            return txt[self.lang]
        def avg_response_time(self):
            resp_list = []
            date_and_time = self.df.date+self.df.time
            for i in range(1, len(self.df)):
                resp_list.append(date_and_time[i]-date_and_time[i-1])
            first_quartile, last_quartile = len(self.df)//4, len(self.df)*3//4
            iqr_mean = sum(resp_list[first_quartile:last_quartile], timedelta(0))/len(resp_list)/2
            seconds, minutes, hours, days = (iqr_mean.seconds%60, iqr_mean >= timedelta(minutes=1), iqr_mean >= timedelta(hours=1), iqr_mean >= timedelta(days=1))
            txt = {"en": f"On average a response to a message arrives:\n{f'{iqr_mean.days} days ' if days else ''}{f'{iqr_mean.seconds//3600} hours ' if hours else ''}"
                       +f"{f'{(iqr_mean.seconds//60)%60} minutes ' if minutes else ''}{f'{iqr_mean.seconds%60} seconds'} later 🏃",
                   "it": f"In media un messaggio arriva:\n{f'{iqr_mean.days} giorni ' if days else ''}{f'{iqr_mean.seconds//3600} ore ' if hours else ''}"
                       +f"{f'{(iqr_mean.seconds//60)%60} minuti ' if minutes else ''}{f'{iqr_mean.seconds%60} secondi'} dopo 🏃"}
            return txt[self.lang]
        def swear_count(self):
            tot = 0
            words_dict = get_message_freq_dict(self.df.message)
            swears = [i[:-1] for i in open(path.join(BASE_DIR, "../../lists/parolacce.txt"), "r")]
            for swear in swears:
                if swear in words_dict.keys():
                    tot += words_dict[swear]
            txt = {"en": f"{tot} swear words have been sent 🤬",
                   "it": f"Sono state dette {tot} parolacce 🤬"}
            return txt[self.lang]
        def avg_message_length(self):
            lst = [len(word) for word in [message.split() for message in self.df.message]]
            avg = round(sum(lst)/len(lst), 2)
            txt = {"en": f"On average there are {avg} words in a message 🔎",
                   "it": f"Ci sono in media {avg} parole in un messaggio 🔎"}
            return txt[self.lang]
        possibilities = ["message_count", "active_days", "messages_per_day", "file_count", "most_active_day", "most_active_year",
                         "most_active_month", "most_active_weekday", "most_active_person", "longest_active_streak",
                         "longest_inactive_streak", "first_texter", "avg_response_time", "swear_count", "avg_message_length"]
        if cat in possibilities:
            txt = eval(cat+"(self)")
        else:
            txt = {"en": "Something went wrong :(",
                   "it": "Qualcosa è andato storto :("}
            txt = txt[self.lang]
        self.set_font_size(11)
        txt_pos = {("right", "one"): GREEN_POS, ("right", "two"): GREEN_POS+1, ("right", "three"): GREEN_POS+1,
                   ("left", "one"): WHITE_POS, ("left", "two"): WHITE_POS-1, ("left", "three"): WHITE_POS-1}
        img_offset = {"right": 2, "left": 5}
        pos_to_color = {"left": "white", "right": "green"}
        y = self.update_y(pos, "message", check_text(txt))
        self.image(name=path.join(PDF_Constructor.img_path, f"{pos_to_color[pos]}_{check_text(txt)}line_bubble.png"),
                   x=txt_pos[(pos, check_text(txt))]-img_offset[pos], y=y-4, w=100)
        self.set_xy(txt_pos[(pos, check_text(txt))], y)
        self.multi_cell(w=WIDTH/2-5, txt=transform_text(txt), h=5)

    def save(self) -> str:
        """Save the PDF to a file and clean up temporary files.

        :return: path to the saved PDF file"""

        if not self.prep(plot=False):
            return
        self.load = 100
        out = {"en": f"Analysis of {self.name if self.group else f'{self.name[0]} and {self.name[1]}'} chat.pdf",
               "it": f"Analisi della chat {self.name if self.group else f'tra {self.name[0]} e {self.name[1]}'}.pdf"}
        out = out[self.lang]
        makedirs(OUTPUT, exist_ok=True)
        output_path = path.join(OUTPUT, out)
        self.output(output_path, "F")
        while self.counter != 0:
            img_path = path.join(OUTPUT, f"{self.counter}.png")
            if path.exists(img_path):
                remove(img_path)
            self.counter -= 1
        possibilities = [
            path.join(INPUT, f"Chat WhatsApp con {self.name if type(self.name) != tuple else self.name[0]}.txt"),
            path.join(INPUT, f"Chat WhatsApp_con_{self.name if type(self.name) != tuple else self.name[0]}.txt"),
            path.join(INPUT, f"WhatsApp Chat - {self.name if type(self.name) != tuple else self.name[0]}.zip"),
            path.join(INPUT, f"WhatsApp_Chat_-_{self.name if type(self.name) != tuple else self.name[0]}.zip"),
            path.join(INPUT, "_chat.txt")
        ]
        for file_path in possibilities:
            if path.exists(file_path):
                remove(file_path)
        return output_path 

    def get_analytics(self) -> dict:
        """Return aggregate analytics about the parsed chat.
        
        :return: dictionary with analytics"""
        
        df = self.df

        total_messages = len(df)
        participants = set(df.who)
        if "info" in participants:
            participants.remove("info")
        participants_count = len(participants)
        is_group = self.group

        start_date = pd.to_datetime(df.date.min()).date() if total_messages else None
        end_date = pd.to_datetime(df.date.max()).date() if total_messages else None
        active_days = len(set(df.date)) if total_messages else 0

        days_range = max(1, len(pd.date_range(df.date.iloc[0], date.today()))) if total_messages else 1
        avg_msgs_per_day = round(total_messages / days_range, 2)

        if total_messages:
            weekday_counts = df.date.dt.dayofweek.value_counts()
            most_active_weekday = int(weekday_counts.idxmax()) if len(weekday_counts) else None
            month_counts = df.date.dt.to_period("M").value_counts()
            most_active_month = str(month_counts.idxmax()) if len(month_counts) else None
        else:
            most_active_weekday = None
            most_active_month = None

        files_shared_count = int(df.message.fillna("").str.contains("<Media", na=False).sum())

        avg_message_length_words = round(
            sum(len(str(m).split()) for m in df.message) / total_messages, 2
        ) if total_messages else 0.0

        
        resp_seconds = None
        if total_messages > 1:
            deltas = (df.date + df.time).diff().dropna()
            if len(deltas) > 0:
                first_q = len(deltas)//4
                last_q = len(deltas)*3//4
                denom = max(1, (last_q-first_q))
                iqr_mean = sum(deltas.iloc[first_q:last_q], timedelta(0)) / denom / 2
                resp_seconds = int(iqr_mean.total_seconds())

        # Use utility functions for complex analytics
        daily_message_counts = get_daily_message_counts(df, interval="day")
        most_used_words = get_most_used_words(df, max_words=100)
        most_used_emojis = get_most_used_emojis(df, max_emojis=15)

        return {
            "total_messages": total_messages,
            "participants_count": participants_count,
            "is_group": bool(is_group),
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
            "active_days": active_days,
            "avg_msgs_per_day": avg_msgs_per_day,
            "most_active_weekday": most_active_weekday,
            "most_active_month": most_active_month,
            "files_shared_count": files_shared_count,
            "avg_message_length_words": avg_message_length_words,
            "response_seconds_typical": resp_seconds,
            "lang": self.lang,
            "daily_message_counts": daily_message_counts,
            "most_used_words": most_used_words,
            "most_used_emojis": most_used_emojis,
        }