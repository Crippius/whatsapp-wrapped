import pandas as pd # To store all the informations inside a Dataframe
import matplotlib.pyplot as plt # To plot all the data in a meaningful way

from matplotlib.font_manager import FontProperties # To work with other fonts inside matplotlib
import matplotlib.dates as mdates # To use different dates format in matplotlib 
from matplotlib import rcParams # To change the font used by matplotliv

from fpdf import FPDF # To create and deploy the PDF that can later be downloaded

import re # To match and group the info inside the message
from emoji import EMOJI_DATA # To validate if a character is an emoji or not
from string import punctuation # To remove all the punctuation in a message
from datetime import date, timedelta # To manipulate the dates we
from shutil import move # To move the pdf inside the correct directory
from os import remove, path # To remove the images created
from math import pi # To use polar coordinates in spider plot

from wordcloud import WordCloud # To remove the images created 

# COLOR PALETTE USED:     #075e55 | #128c7f |  #26d367 | #dcf8c7 | #ece5dd 
#                         seagreen|bluechill|whatsgreen|palegreen|platinum
#                             ^    (bordef)       ^    (background)   ^                                                                    
#                 top bar color      primary color, used for      used for white
#                  + microphone         graphs and messages           messages

HEIGHT = 297 # Height of PDF
WIDTH = 210 # Width of PDF

GREEN_POS = 108 # Position of green ONELINE bubble message
WHITE_POS = 8   # Position of white ONELINE bubble message

WINDOW_LENGTH = 5 # Dimension of window for rolling average
PLOT_HEIGHT = 75 # Height of plot inside PDF
CHAR_PER_LINE = 50

LEFT_PLOT = 5 # Plot in left side of PDF
RIGHT_PLOT = 5+WIDTH/2 # right side of PDF



def IOS_or_Android(txt, regexs):

    for regex in regexs["IOS"].values():
        if re.search(regex, txt) != None:
            return "IOS"
    for regex in regexs["Android"].values():
        if re.search(regex, txt) != None:
            return "Android"
    print(txt)
    return "IDK"

def get_data(file:str) -> list: # DESCRIPTION: extract the info inside the .txt file
    # PARAMETERS: file (str) = file that is going to be extracted
    # RETURNS: list of lists, where each sublist contains [date, time, sender, message] for every message

    fp = open(file, "r", encoding="utf8")
    data = []

    trame = fp.readline()

    regexs = {"IOS":{"normal":"\[(\d{2}\/\d{2}\/\d{2}), (\d{2}:\d{2}:\d{2})\] (.*): (.*)$",
                     "info":"\[(\d{2}\/\d{2}\/\d{2}), (\d{2}:\d{2}:\d{2})\] (.*)$"},
          "Android":{"normal":"(\d{2}\/\d{2}\/\d{2}), (\d{2}:\d{2}) - (.*): (.*)$",
                     "info":"(\d{2}\/\d{2}\/\d{2}), (\d{2}:\d{2}) - (.*)$"}}

    device = IOS_or_Android(trame, regexs)

    while trame != "": # Read file till EOF        .--- Regex to match with trame (header + payload)
                       #                           v
        norm = re.search(regexs[device]["normal"], trame)
        info = re.search(regexs[device]["info"], trame)

        if norm != None or info != None: 
            if norm != None: # Normal message
                date = norm.group(1)
                time = norm.group(2)
                who = norm.group(3)
                message = norm.group(4)
            else:
                date = info.group(1)
                time = info.group(2)
                who = "info"
                message = info.group(3)
            
            if device == "Android":
                time += ":00"
            if message.find("‎") != -1:
                message = message[message.find("‎")+1:]
            data.append([date, time, who, message]) # Appending data into big list
            
        elif len(data) != 0: # Multiline message, add it to last part of message (condition added to avoid crashes)
                data[-1][3] += "\n"+trame

        trame = fp.readline()

    return data


def spider_plot(categories:list, values:list) -> None: # DESCRIPTION: Create spider plot 
    # PARAMETERS: categories (list): labels to add on top of plot | values (list): values that need to be plotted

    angles = [n / float(len(categories)) * 2 * pi for n in range(len(categories))] # Getting angles
    
    angles += angles[:1] # Adding first value to both lists (needed to close the circle)
    values += values[:1] 

    ax = plt.subplot(111, polar=True)
    plt.xticks(angles[:-1], categories, size=11)

    ax.set_rlabel_position(0)
    first_digit = int(str(max(values))[0]) # Setting up labels to read the graph better
    if first_digit < 5:
        labels = [i*10**(len(str(max(values)))-1) for i in [j for j in (1, 2, 3, 4) if j*6/5<first_digit]] + [max(values)]
    else:
        labels = [i*10**(len(str(max(values)))-1) for i in [j for j in (2, 4, 6, 8) if j*6/5<first_digit]] + [max(values)]

    plt.yticks(labels, [str(i) for i in labels], color="grey", size=7)
    plt.ylim(0,max(values)*12/10)
    
    ax.plot(angles, values, linewidth=1, linestyle='solid', color="#128c7f")
    ax.fill(angles, values, alpha=0.5, color="#26d367") # Creating plot


def inverted_barh_plot(y:list, x:list) -> None: # DESCRIPTION: Invert barh plot (instead of left to right -> right to left):
    # PARAMETERS: y (list): labels for barh plot | x (list): values of barh plot            |########     ->       #######|                                                                     |###          ->           ###|

    fig, ax = plt.subplots() 

    ax.barh(y, x, align='center', color='#26d367')
    ax.set_yticks([]) # Removing labels
    ax.set_yticklabels([])

    ax.invert_yaxis()
    ax.invert_xaxis() # Inverting axes
    ax2 = ax.twinx()

    ax2.set_ylim(ax.get_ylim())
    ax2.set_yticks(y) # Setting up labels again


def add_labels_to_bar(plot:plt, labels:list, font_size:int=18, dir:str="vertical", pos:str="external") -> None: 
    # DESCRIPTION: Adds auxiliary labels near the sides of the bars 
    # PARAMETERS: plot (plt) = plot in which the labels need to be added | labels (str) = string that need to be annotated
    # prop (font) = font used to write labels | font_size (int) = size of font | dir (str) = direction of plot (horizontal or vertical)
    # pos (str) = put labels on top of bar or just outside it (internal or external)

    #TODO: add external/internal options to vertical bars
    if dir == "vertical": 
        plt.ylim(0, plt.ylim()[1]+plt.ylim()[1]/10) # Make plot larger to create space for labels
        maxi = max([rect1.get_height() for rect1 in plot]) # Biggest y value in plot

        for rect1, label in zip(plot, labels): 
            plt.annotate(
                label, 
                (rect1.get_x() + rect1.get_width()/2, rect1.get_height()+maxi/100), # x and y positions
                ha="center",
                va="bottom",
                fontsize=font_size
            )
            
    else: 
        plt.xlim(0, plt.xlim()[1]+plt.xlim()[1]/10)
        maxi = max([rect1.get_y() for rect1 in plot]) # Biggest x value in plot

        for rect1, label in zip(plot, labels):

            if pos == "external":
                x = rect1.get_y() + rect1.get_width()+maxi/100
                ha = "right"
            else:
                x = plt.xlim()[1]/50
                ha = "left"

            plt.annotate(
                label,
                (x, rect1.get_y()),
                ha=ha,
                va="bottom",
                fontsize=font_size,
            )
    
    return


def remove_header(df:pd.DataFrame) -> pd.DataFrame:
    return df[3:].reset_index() # It should check if the header is present, but for now the function just removes the first messages


def get_message_freq_dict(messages:pd.Series, blacklist:list=[]) -> dict: # DESCRIPTION: Create dict with frequency of words
    # PARAMETERS: messages (Series): list of strings of messages | blacklist (list): if wanted don't consider some words

    most_used_words = {} # Similar to emoji plot, create dict with all words where the value of each key is the number of times it was written
    for message in messages: #
        for word in [word.lower() for word in message.split()]:
            word = word.translate(str.maketrans('', '', punctuation)) # Stripping away punctuation
            if word not in blacklist and word != "":
                if word not in most_used_words:
                    most_used_words[word] = 0
                most_used_words[word] += 1
    return most_used_words


def get_swear_count(messages:pd.Series) -> int: # DESCRIPTION: count number of swears inside list of messages
    # PARAMETERS: messages (Series): list of strings
    # RETURNS: int (number of swears)

    tot = 0
    words_dict = get_message_freq_dict(messages)
    swears = [i[:-1] for i in open("parolacce.txt", "r")]
    for swear in swears:
        if swear in words_dict.keys():
            tot += words_dict[swear]
    return tot


def get_average_response_time(df:pd.DataFrame) -> str: # DESCRIPTION: Returns the average time in which someone responds to a message
    # PARAMETERS: df (Dataframe): table from which the info is gained

    resp_list = []
    date_and_time = df.date+df.time

    for i in range(1, len(df)): # Getting difference between the time of the messages
        resp_list.append(date_and_time[i]-date_and_time[i-1])

    first_quartile, last_quartile = len(df)//4, len(df)*3//4 # Getting the interquartile mean, since outliers could skew the average too much
    iqr_mean = sum(resp_list[first_quartile:last_quartile], timedelta(0))/len(resp_list)/2

    txt = f"{iqr_mean.days} giorni " if iqr_mean >= timedelta(days=1) else "" # Writing the message
    txt += f"{iqr_mean.seconds//3600} ore " if iqr_mean >= timedelta(hours=1) else ""
    txt += f"{(iqr_mean.seconds//60)%60} minuti " if iqr_mean >= timedelta(minutes=1) else ""
    txt += "e " if len(txt) != 0 else ""
    txt += f"{iqr_mean.seconds%60} secondi"
    return txt
    

def concentrate_values(in_dict:dict, max_values:int, others:bool) -> dict: 
    # DESCRIPTION: make dictionary smaller by remvoing keys with smaller values
    # PARAMETERS: in_dict (dict) = dictionary that is going to be modified | max_values (int) = number of unique dict keys
    # others (bool) = add additional key with sum of values of the last keys in it

    if len(in_dict.keys()) <= max_values: # If dict already smaller than the maximum value, don't modify it
        return in_dict
    
    out_dict = {}
    for i in list(in_dict.keys())[:max_values-others]:
        out_dict[i] = in_dict[i]
    
    if others:                                                                                          # N.B. "altri" == "others"
        if len(list(in_dict.keys())[max_values-others:]) == 1: # Edge case: when only one key is remaining, don't show "Altri", but the key
            out_dict[list(in_dict.keys())[max_values-others]] = in_dict[list(in_dict.keys())[max_values-others]]
        else:
            out_dict["Altri"] = sum([i for i in list(in_dict.values())[max_values-others:]])
    
    return out_dict


def sort_dict(in_dict:dict, max_values:int=-1, reverse:bool=True, others:bool=True) -> dict: 
    # DESCRIPTION: Given a dict, it sorts its keys by its values (and concentrates them if its wanted)
    # PARAMETERS: in_dict (dict) = dictionary that is modified | max_values (int) = number of unique dict keys (if -1 no maximum)
    # reverse (bool) = return dict in decreasing order if true | others (bool) = include condensed keys w/ smaller keys

    out_dict = {}
    sorted_keys = sorted(in_dict, key=in_dict.get, reverse=True) 
    for w in sorted_keys:
        out_dict[w] = in_dict[w]

    if max_values != -1: # Concentrating keys (if wanted)
        out_dict = concentrate_values(out_dict, max_values, others)

    if reverse: # Reversing (if true)
        out_dict = {k:out_dict[k] for k in list(out_dict.keys())[::-1]}

    return out_dict


def max_and_index(lst:list) -> tuple: # DESCRIPTION: returns the maximum value and the index in which it is placed
    # PARAMETERS: lst (list): list that needs to be checked
    # RETURNS: tuple (int, int): maximum value and its index in the list

    best = float("-inf")
    best_index = -1
    for i in range(len(lst)):
        if type(lst[i]) != int:
            continue
        if lst[i] > best:
            best = lst[i]
            best_index = i
    return best, best_index


def get_longest_active_streak(dates:list) -> tuple: # DESCRIPTION: returns the longest streak of days where the group was active
    # PARAMETERS: dates (list): list of days in which a message was sent (only unique values are sent)
    # RETURNS: the start of the streak and its end (datetime form) + integer which stores the longest streak

    dates = sorted(dates)

    start = dates[0]
    end = dates[0]
    best_streak = 0
    curr_streak = 0

    for i in range(1, len(dates)):
        if dates[i]-dates[i-1] != timedelta(days=1): # If the gap between days isn't equal to a day, the streak ends, 
            if curr_streak > best_streak:            # check if streak big enough to replace previous one, reset counter
                best_streak = curr_streak
                start = dates[i-1-curr_streak]
                end = dates[i-1]
            curr_streak = 0
        else:
            curr_streak += 1

    return start, end, best_streak


def get_longest_inactive_streak(dates:list): # DESCRIPTION: returns the longest streak of days where the group was inactive
    # PARAMETERS: dates (list): list of days in which a message was sent
    # RETURNS: the start of the streak and its end (datetime form) + integer which stores the longest streak

    dates = sorted(dates)

    start = "01/01/1900"
    end = "01/01/1900"
    best_streak = timedelta(days=1)
    for i in range(1, len(dates)):
        if dates[i]-dates[i-1] > best_streak: # If the gap between days is larger than the previous one
            start = dates[i-1]                # replace it and reset counter
            end = dates[i]
            best_streak = dates[i]-dates[i-1]
    return start, end, best_streak.days


def get_first_texter(df): 
    # DESCRIPTION: Get who is more prone to text first (by incrementing the value of the first person that writes in a day)
    # (I know it's not totally correct, but using an unstable threshold like '2 hours between messages' seemed worse)
    # PARAMETERS: df (Dataframe): from which the data is collected

    people = {}
    for i in range(1, len(df)):
        if df.date[i] != df.date[i-1]:
            who = df.who[i]
            if who not in people:
                people[who] = 0
            people[who] += 1
    people = sort_dict(people, 1, others=False)
    return list(people.keys())[0]


def check_text(txt:str): # DESCRIPTION: Checks how big the message bubble needs to be
    # PARAMETERS txt (str): text that is going to be checked
    # RETURNS: str (one, two, three), it depends on how big the message is

    bubble = 1
    counter = 0
    for i in txt:
        if counter == CHAR_PER_LINE-1 or i == "\n": # If counter reaches limit of characters per line or a line break,
            bubble += 1                             # increment bubble height and reset counter
            if bubble == 3:
                break
            counter = -1
        counter += 1

    bubble_dict = {1:"one", 2:"two", 3:"three"}
    return bubble_dict[bubble]


def transform_text(txt:str): # DESCRIPTION: Transform string of text to fit into message bubble
    # PARAMETERS txt (str): text that is going to be tranformed

    new_txt = ""
    counter = 0
    times = 0
    for i in txt:
        if counter == CHAR_PER_LINE or i == "\n":
            counter = -1
            times += 1
            if times == 3:
                break
            new_txt += "\n"
        
        if i != "\n":
            new_txt += i
        counter += 1

    return new_txt
    
    

class PDF_Constructor(FPDF): # Main class that is used in this program, inherits FPDF class, adding new functionalities

    def __init__(self, file): 
        # DESCRIPTION: Initialize class, with FPDF's initialization a dataframe is created and cleaned,
        # the group (or chatters) name and a counter are stored, Structure with basic info is built
        
        if not path.exists(file):
            print("No such file exists")
            self.ok = 0
        else:
            self.ok = 1

        FPDF.__init__(self) 

        self.counter = 0

        self.df = pd.DataFrame(get_data(file), columns=["date", "time", "who", "message"]) # Creating Dataframe
        self.df.date = pd.to_datetime(self.df.date, format="%d/%m/%y") # Setting dtypes
        self.df.time = pd.to_timedelta(self.df.time)

        self.df = remove_header(self.df) # When people change phone and don't have a backup for their whatsapp messages, 
                                # all of their previous conversations are eliminated, but the "X created this group" message;
                                # when plotting the number of messages per interval, this can create an ugly plot, this function avoids that

        m = re.search("Chat WhatsApp con (.+?).txt", file) # Catching name of group chat
        self.name = m.group(1) if m != None else ""
        self.group = True

        if len(set(self.df.who)) == 3 and "info" in set(self.df.who): # <- If it's a private chat
            self.group = False # NOT a group chat
            lst = list(set(self.df.who))
            lst.pop("info")
            self.name = tuple([lst[lst.index(self.name)], lst[not lst.index(self.name)]]) # self.group contains name of two chatters
            

        self.plot_pos = {"left":LEFT_PLOT, "right":RIGHT_PLOT} # Used later to format plot into pdf

        self.pos = {"left":0, "right":0} # Variables that keep track where "the pointer" is at, for the left and right sides of the pdf
        self.last = {"left":None, "right":None} # They keep track of the last positioned object

        prop=FontProperties(fname='my_fonts/seguiemj.ttf') # Changing matplotib and fpdf font
        rcParams['font.family'] = prop.get_name()
        self.add_font('seguiemj', '', "my_fonts/seguiemj.ttf")
        self.set_font('seguiemj', '', 16)

        self.add_structure() # Adding the structure of the pdf


    def add_structure(self): # DESCRIPTION: Adding the background of the pdf + aestethics

        self.add_page()

        self.image('images/background.png', x = 0, y = 0, w = WIDTH, h = HEIGHT)
        self.image('images/top_level.png', x = 0, y = 0, w = WIDTH)

        self.cell(15, 0, "")
        self.set_text_color(255, 255, 255)  # Adding top part
        if self.group:
            self.multi_cell(WIDTH-70, 0, transform_text(f'Analisi della chat {self.name}'))
        else:
            self.multi_cell(WIDTH-70, 0, f'Analisi della chat tra {self.name[0]} e {self.name[1]}'[:CHAR_PER_LINE])
        self.set_text_color(0, 0, 0)

        x, y = self.get_x(), self.get_y()
        self.set_auto_page_break(False)
        self.set_y(-20)

        self.image("images/writing_box.png", x=20, y=self.get_y()-4, w=WIDTH-40) # Adding footer
        self.cell(30 , 0)
        self.set_font_size(12)
        self.multi_cell(0, 5, "Vuoi creare il wrapped di una tua chat? 🤨" + "\n" + "Vai su http://whatsapp_wrapped.it 👈", align="L", link="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        self.set_xy(x, y)


    def update_counter(self) -> None: # Simple function that updates counter
        self.counter += 1
    

    def add_image(self, x:int, y:int) -> None: # Adds image to pdf file, given x and y coordinates
        self.image(f"{self.counter}.png", x = x, y = y, w = WIDTH/2 - 5, h=PLOT_HEIGHT)

    
    def prep(self, plot:bool=True) -> bool: # DESCRIPTION: Does necessary preparations before starting function
        # PARAMETERS: plot (bool): updates counter and closes last plot before starting if True

        if self.ok:
            if plot:
                self.update_counter()
                plt.close()
            return True
        else:
            return False
        

    def update_y(self, pos:str, obj:str, lines:str="one") -> int: 
        # DESCRIPTION: Important function that updates the pointer for the left and right sides of the pdf
        # PARAMETERS: pos ("left"/"right") = position in the pdf | obj ("message"/"plot") = current object that needs to be placed
        # lines (only for messages) = number of lines a message has

        mess_dict = {"one":12, "two":20, "three":25} # Padding needed to not overlap from last element
        obj_dict = {(None, "message"):30, (None, "plot"):20,            
                    ("plot", "message"):80, ("plot", "plot"):75, # format (last_element, current_element)
                    ("message", "message"):mess_dict[lines]+5, ("message", "plot"):mess_dict[lines]+5}
        
        self.pos[pos] += obj_dict[(self.last[pos], obj)] # Updating y position of pointer
        self.last[pos] = obj
        return self.pos[pos]
                


    def add_message(self, type:str, pos:str) -> None: # DESCRIPTION: add simple info in a similar fashion to a whatsapp message
        # PARAMETERS: type (str) = type of message to write, available types listed inside of if-else list
        # x, y (int) = coordinates inside of PDF file

        # Dictionaries don't work :(, seems like if-else conditons is the only way to go, even if ugly 
        # Most operations are difficult to read, but are really similar to the ones used in plot, check comments 
        # inside those functions for explanation

        if not self.prep(plot=False):
            return


        if type == "message_count":
            aux = len(self.df) if len(self.df) < 39999 else '40000+'
            txt = f"Sono stati mandati {aux} messaggi!\nVi scrivete un botto! 🤩"
        elif type == "active_days":
            aux = len(set(self.df.date))
            txt = f"Vi siete scritti in {aux} giorni diversi! 🧐"
        elif type == "messages_per_day":
            aux = round(len(self.df)/len(pd.date_range(self.df.date[0], date.today())), 2)
            txt = f"In media vi mandate {aux} messaggi al giorno 📱"
        elif type == "file_count":
            aux = len(self.df[self.df.message == '<Media omessi>'])
            txt = f"Sono stati inviati {aux} file!"
        elif type == "most_active_day":
            aux = max([len(self.df[self.df.date == i]) for i in set(self.df.date)])
            txt = f"Il giorno più attivo è stato il {self.df.loc[aux].date.strftime('%d/%m/%y')}\n{aux} messaggi in totale, che giornata 🤯"
        elif type == "most_active_year":
            aux1, aux2 = max_and_index([len(self.df[self.df.date.dt.year == i]) for i in set(self.df.date.dt.year)])
            txt = f"Anno più attivo: {list(set(self.df.date.dt.year))[aux2]} ({aux1} messaggi)\nChe memorie 💭"
        elif type == "most_active_month":
            aux1, aux2 = max_and_index([len(self.df[self.df.date.dt.to_period('M').dt.to_timestamp() == i]) for i in set(self.df.date.dt.to_period('M').dt.to_timestamp())])
            txt = f"Mese più attivo: 👇🏻\n{list(set(self.df.date.dt.to_period('M').dt.to_timestamp()))[aux2].strftime('%m/%y')} ({aux1} messaggi)"
        elif type == "most_active_weekday":
            aux1, aux2 = max_and_index([len(self.df[self.df.date.dt.day_name() == i]) for i in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]])
            txt =  f'Giorno più attivo: {["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"][aux2]} ({aux1} messaggi)'
        elif type == "most_active_person":
            aux1, aux2 = list(sort_dict({k:len(self.df[self.df.who == k]) for k in set(self.df.who)}, 1, others=False).items())[0]
            txt = f"{aux1} è la persona più attiva!\n Ha scritto {aux2} messaggi ({100*round(aux2/len(self.df), 2)} del totale) 🤙🏻"
        elif type == "longest_active_streak":
            aux1, aux2, aux3 = get_longest_active_streak(list(set(self.df.date)))
            txt = f"Streak di giorni attivi più lunga: {aux3} giorni\nDal {aux1.strftime('%d/%m/%y')} al {aux2.strftime('%d/%m/%y')} ❤️"
        elif type == "longest_inactive_streak":
            aux1, aux2, aux3 = get_longest_inactive_streak(list(set(self.df.date)))
            txt = f"Streak di giorni inattivi più lunga: {aux3} giorni\nDal {aux1.strftime('%d/%m/%y')} al {aux2.strftime('%d/%m/%y')} ☠️"
        elif type == "first_texter":
            aux = get_first_texter(self.df)
            txt = f"Solitamente è {aux} che scrive per prim*... 🥇"
        elif type == "avg_response_time":
            aux = get_average_response_time(self.df)
            txt = f"In media la risposta a un messaggio arriva:\n{aux} dopo 🏃"
        elif type == "swear_count":
            aux = get_swear_count(self.df.message)
            txt = f"Sono state dette {aux} parolacce 🤬"
        elif type == "avg_message_length":
            aux = [len(word) for word in [message.split() for message in self.df.message]]
            txt = f"Ci sono in media {round(sum(aux)/len(aux), 2)} parole in un messaggio 🔎"
        else:
            txt = "Something went wrong :("


        self.set_font_size(11)
        txt_pos = {("right", "one"):GREEN_POS, ("right", "two"):GREEN_POS+1, ("right", "three"):GREEN_POS+1,
                   ("left", "one"):WHITE_POS, ("left", "two"):WHITE_POS-1, ("left", "three"):WHITE_POS-1}
        img_offset = {"right":2, "left":5} # Setting format of message
        pos_to_color = {"left":"white", "right":"green"}

        y = self.update_y(pos, "message", check_text(txt))
   
        self.image(name=f"images/{pos_to_color[pos]}_{check_text(txt)}line_bubble.png", # Putting bubble image
                    x=txt_pos[(pos, check_text(txt))]-img_offset[pos], y=y-4, w=100)

        self.set_xy(txt_pos[(pos, check_text(txt))], y)
        self.multi_cell(w=WIDTH/2-5, txt=transform_text(txt), h=5) # Putting text inside bubble


    def plot_emojis(self, pos:str, who:str="", reverse:bool=False) -> None: 
        # DESCRIPTION: plot most used emojis in chat, place them in PDF given x/y coordinates
        # PARAMETERS: pos ("left"/"right") = position in the pdf | who (str) = if used get emojis of only x character
        # reverse (bool) = if true create barh plot from right to left
        
        if not self.prep():
            return

        if who == "" or not who in self.df.who.unique():
            messages = self.df.message
        else:
            messages = self.df[self.df.who == who].message
    

        emojis = {} # Add all emojis used in chat inside a dictionary, where the value stored is the number of times it has been used
        for message in messages:
            for char in message:
                if char in EMOJI_DATA:
                    if char not in emojis:
                        emojis[char] = 0
                    emojis[char] += 1
        if "🏻" in emojis: # Remove default character
            emojis.pop("🏻")
        if "🏼" in emojis: # <- Totally different character from last if statement...
            emojis.pop("🏼")

        emojis = sort_dict(emojis, 7, reverse=reverse, others=False)

        if len(emojis.keys()) == 0: # Adding a pair inside the empty dict to avoid crash
            emojis["🏼"] = 0

        plt.title("Emoji più utilizzate:") # Plotting
        plot = plt.bar(emojis.keys(), emojis.values(), color="#26d367")
        plt.xticks(fontsize=20)
        plt.text(x=plt.xlim()[0]+1 if reverse else plt.xlim()[1]-1, y=plt.ylim()[1]*9/10, s=f"{sum(emojis.values())} emoji\ntotali 😯", 
                 ha="left" if reverse else "right", va="top", fontsize=16,
                 bbox=dict(facecolor='none', edgecolor='black', boxstyle='round,pad=1'))


        emojis_to_size_dict = {1:28, 2:26, 3:24, 4:22, 5:21, 6:20, 7:18, 8:16, 9:14, 10:12} # Different sizes of unique emojis create different graphs
        add_labels_to_bar(plot, emojis.values(), font_size=emojis_to_size_dict[len(emojis)], dir="vertical")

        plt.savefig(str(self.counter), transparent=True)
        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))


    def plot_number_of_messages(self, pos:str, interval:str="day") -> None: 
        # DESCRIPTION: create plot in which are displayed the number of messages sent in a given timeframe (from days to years), and add it to PDF
        # PARAMETERS: pos ("left"/"right") = position in the pdf | interval (day/week/month/year) = interval messages are stored

        if not self.prep():
            return

        x_dict = {"day":pd.date_range(self.df.date[0], date.today(), freq="D"), # Getting range of all dates from first message to today 
                  "week":pd.date_range(self.df.date[0]-pd.tseries.offsets.Week(1), date.today(), freq="W-MON"),
                  "month":pd.date_range(self.df.date[0]-pd.tseries.offsets.MonthBegin(1), date.today(), freq="MS"), 
                  "year":pd.date_range(self.df.date[0]-pd.tseries.offsets.YearBegin(1), date.today(), freq="YS")}
        
        if interval not in x_dict:
            return

        x_pos = x_dict[interval] # Get the correct interval from the possibilities
        y_pos = []
        running_average = []
        window = []

        for i in x_pos: # Getting the points
            if interval == "day":
                point = len(self.df[self.df.date == i])
            elif interval == "week":
                point = len(self.df[self.df.date - self.df.date.dt.weekday * timedelta(days=1) == i])
            elif interval == "month":
                point = len(self.df[self.df.date.dt.to_period('M').dt.to_timestamp() == i])
            elif interval == "year":
                point = len(self.df[self.df.date.dt.to_period('Y').dt.to_timestamp() == i])

            if len(window) == 0: # Running average initialization
                window = [point*(WINDOW_LENGTH)**(-1)]*WINDOW_LENGTH
            y_pos.append(point)
            window.pop(0)
            window.append(point)
            running_average.append((sum(window)) / WINDOW_LENGTH)
        
        plt.plot(x_pos, y_pos, color="#26d367") # Plotting

        if interval != "year": # Plot running average
            plt.plot(x_pos, running_average, color="#075e55") # Changing format of dates to avoid overlapping
            if pd.to_datetime(x_pos[-1])-pd.to_datetime(x_pos[0]) < timedelta(days=365):
                if pd.to_datetime(x_pos[-1])-pd.to_datetime(x_pos[0]) < timedelta(days=365//2):
                    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
                else:
                    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%y'))
            
        plt.grid(axis="y")
        translator = {"day":"giorno", "week":"settimana", "month":"mese", "year":"anno"}
        plt.title(f"Numero di messaggi per ogni {translator[interval]}:")
        
        plt.savefig(str(self.counter), transparent=True)
        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))
    

    def plot_day_of_the_week(self, pos:str) -> None: # DESCRIPTION: Plotting number of messages sent per weekday
        # PARAMETERS: pos ("left"/"right") = position in the pdf

        if not self.prep():
            return

        weekday = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] # English (used in functions)
        x_pos = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"] # Italian (displayed in plot)
        y_pos = [len(self.df[self.df.date.dt.day_name() == i]) for i in weekday]

        spider_plot(x_pos, y_pos)
        plt.title("Numero di messaggi per giorno della settimana:", pad=30)
        plt.savefig(str(self.counter), transparent=True)
        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))
                
    

    def plot_most_used_words(self, pos:str, wordcloud:bool=True) -> None: # DESCRIPTION: Barplot with most used words
        # PARAMETERS: pos ("left"/"right") = position in the pdf | wordcloud (bool) = use barplot or wordcloud

        if not self.prep():
            return
        
        blacklist = [i[:-1] for i in open("blacklist.txt", "r").readlines()] + ["è"] # Used to get rid of boring words (articles, prepositions...)
        most_used_words = get_message_freq_dict(self.df.message, blacklist=blacklist)

        if wordcloud: # Creating word cloud
            plot = WordCloud(width=400, height=300, max_words=100, stopwords=blacklist, min_font_size=6,
                             background_color=None, mode="RGBA", colormap="summer").generate_from_frequencies(most_used_words)
            plt.imshow(plot, interpolation="bilinear")
            plt.axis("on")
            plt.xticks([]) # Removing ticks (useless) 
            plt.yticks([])
        else:
            plt.bar(list(most_used_words.keys()), most_used_words.values(), color="#26d367")
        
        plt.title("Parole più utilizzate:")
        plt.savefig(str(self.counter), transparent=True)
        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))
    

    def plot_most_active_people(self, pos:str) -> None: # DESCRIPTION: Plot most number of messages sent per person
        # PARAMETERS: pos ("left"/"right") = position in the pdf

        if not self.prep():
            return

        people = {k:len(self.df[self.df.who == k]) for k in set(self.df.who)} # Dict {person:number of messages}
        if "info" in people.keys():
            people.pop("info")
        people = sort_dict(people, 7, reverse=True)
        
        if self.group: # If group chat use barplot
            plt.title(f"Persone più attive in {self.name}:")
            set_to_font_size = {1:150, 2:45, 3:40, 4:35, 5:32, 6:25, 7:21, 8:18, 9:15, 10:14} # Different sizes of people create different graphs
            plot = plt.barh([str(i) for i in people.values()], people.values(), color="#26d367")
            add_labels_to_bar(plot, people.keys(), font_size=set_to_font_size[len(people)], dir="horizontal", pos="internal")

        else: # If private chat use pie plot
            plt.title(f"Numero di messaggi inviati")
            plt.pie(x=people.values(), labels=people.keys(), colors=("#26d367", "#128c7f"), textprops={"fontsize":14},
                    autopct=lambda x: f"{int(round((x/100)*sum(people.values()), 0))} messaggi\n({round(x, 2)}%)")

        plt.savefig(str(self.counter), transparent=True)
        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))


    def plot_time_of_messages(self, pos:str): # DESCRIPTION: Plot number of messages per time period
        # PARAMETERS: pos ("left"/"right") = position in the pdf

        if not self.prep():
            return

        plt.title("Numero di messaggio per periodo del giorno:")

        x_pos = [timedelta(hours=i//2, minutes=30*(i%2)) for i in range(0, 48)]
        x_pos = x_pos[6:]+x_pos[:6] 
        slotted_times = [i.floor("30min") for i in self.df.time]

        y_pos = [slotted_times.count(i) for i in x_pos]
        x_pos = [f"{'0' if i < timedelta(hours=10) else ''}{str(i)[:-3]}"for i in x_pos] # Changing xticks to make them easier to look at in plot

        plt.plot_date(x_pos, y_pos, color="#128c7f")
        plt.grid(axis="y")
        plt.fill_between(x_pos, y_pos, color="#26d367")

        N=6 # Spacing xticks to avoid overlapping
        x_pos = [x_pos[i] if not i%N else "" for i in range(len(x_pos))]
        plt.xticks(x_pos)
        
        plt.savefig(str(self.counter), transparent=True)

        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))
    
    
    def save(self) -> None: # DESCRIPTION: Save file if nothing has gone wrong, remove images created
        if not self.prep(plot=False):
            return

        out = f"Analisi della chat {self.name if self.group else f'tra {self.name[0]} e {self.name[1]}'}.pdf"
        self.output(f'{out}')
        move(f'{out}', f'pdfs/{out}')
        while self.counter != 0:
            if path.exists(f"{self.counter}.png"):
                remove(f"{self.counter}.png")
            self.counter -= 1




def seed1(pdf:PDF_Constructor): # One possible combination of plot and messages (for group chats)
    
    pdf.plot_number_of_messages(interval="day", pos="left")

    pdf.add_message(type="most_active_day", pos="left")

    pdf.plot_emojis(pos="left")

    pdf.plot_most_active_people(pos="left")

    pdf.add_message(type="message_count", pos="right")

    pdf.plot_time_of_messages(pos="right")

    pdf.add_message(type="longest_active_streak", pos="right")

    pdf.add_message(type="longest_inactive_streak", pos="right")

    pdf.plot_most_used_words(pos="right", wordcloud=True)

    pdf.add_message(type="avg_response_time", pos="right")


def seed2(pdf:PDF_Constructor): # Another possible combination (for private chats)
    
    pdf.plot_emojis("left", who=pdf.name[0])
    pdf.plot_emojis("right", who=pdf.name[1], reverse=True)
    pdf.plot_number_of_messages("left")
    pdf.plot_time_of_messages("right")
    pdf.plot_most_active_people("left")



def main(file): 
    
    pdf = PDF_Constructor(file)

    if not pdf.group: # Private chat (two real people + info)
        seed2(pdf)
    else:
        seed1(pdf)

    pdf.save()

if __name__ == "__main__":
    file = "text_files/Chat WhatsApp con 3A.txt"
    main(file)