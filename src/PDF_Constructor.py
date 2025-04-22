# TODO: Add dynamic loading bar (use same library of wordle project)
# TODO: create new seeds
# TODO: Add error handler

import pandas as pd # To store all the informations inside a Dataframe
import matplotlib
matplotlib.use('Agg')
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
from zipfile import ZipFile # To unzip a zip file
from math import pi # To use polar coordinates in spider plot
from wordcloud import WordCloud # To remove the images created 

# COLOR PALETTE USED:     #075e55 | #128c7f |  #26d367 | #dcf8c7 | #ece5dd 
#                         seagreen|bluechill|whatsgreen|palegreen|platinum
#                             ^    (border)       ^    (background)   ^                                                                    
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

def font_friendly(txt:str) -> str: # DESCRIPTION: Change string by removing of all bad emojis that make the PDF look bad (LIST COULD BE UPDATED)
    # PARAMETERS: txt (str) = text that needs to be modified

    bad_emojis = ["️", "⃣", "🏽", "🏼", "🏾", "🏻", "🏿"]
    new_txt = ""
    for i in txt:
        if i not in bad_emojis:
            new_txt += i
    
    return new_txt

def IOS_or_Android(txt:str, regexs:dict) -> str: 
    # DESCRIPTION: Return from which device the file is from (Android or iPhone) by checking the text to some regexs
    # PARAMETERS: txt (str) = text that gets checked 
    # regexs (dict) = dictionary where the key is the device (Android/IOS) and values are some regexs used for each one 

    for regex in regexs["IOS"].values():
        if re.search(regex, txt) != None:
            return "IOS"
    for regex in regexs["Android"].values():
        if re.search(regex, txt) != None:
            return "Android"

    return "IDK"

def get_data(file:str) -> list: # DESCRIPTION: extract the info inside the .txt file
    # PARAMETERS: file (str) = file that is going to be extracted
    # RETURNS: list of lists, where each sublist contains [date, time, sender, message] for every message

    fp = open(file, "r", encoding="utf8")
    data = []

    trame = fp.readline()

    regexs = {"IOS":{"normal":"\[(\d{2}\/\d{2}\/\d{2}), (\d{2}:\d{2}:\d{2})\] (.*?): (.*)$",
                     "info":"\[(\d{2}\/\d{2}\/\d{2}), (\d{2}:\d{2}:\d{2})\] (.*)$"},
          "Android":{"normal":"(\d{2}\/\d{2}\/\d{2}), (\d{2}:\d{2}) - (.*?): (.*)$",
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
                who = font_friendly(norm.group(3))
                message = norm.group(4)
            else:
                date = info.group(1)
                time = info.group(2)
                who = "info"
                message = info.group(3)
            
            if device == "Android":
                time += ":00"
            
            
            while message.find("‎") != -1:
                message = message[:message.find("‎")]+message[message.find("‎")+1:]
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
        return df[3:].reset_index() if len(df) > 3 else df 
        # It should check if the header is present, but for now the function just removes the first messages (TO BE UPDATED)
    

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


def concentrate_values(in_dict:dict, max_values:int, others:bool, lang="en") -> dict: 
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
            txt = {"en":"Others", "it":"Altri"}
            out_dict[txt[lang]] = sum([i for i in list(in_dict.values())[max_values-others:]])
    
    return out_dict


def sort_dict(in_dict:dict, max_values:int=-1, reverse:bool=True, others:bool=True, lang="en") -> dict: 
    # DESCRIPTION: Given a dict, it sorts its keys by its values (and concentrates them if its wanted)
    # PARAMETERS: in_dict (dict) = dictionary that is modified | max_values (int) = number of unique dict keys (if -1 no maximum)
    # reverse (bool) = return dict in decreasing order if true | others (bool) = include condensed keys w/ smaller keys

    out_dict = {}
    sorted_keys = sorted(in_dict, key=in_dict.get, reverse=True) 
    for w in sorted_keys:
        out_dict[w] = in_dict[w]

    if max_values != -1: # Concentrating keys (if wanted)
        out_dict = concentrate_values(out_dict, max_values, others, lang)

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

    img_path = "../static/"
    
    def __init__(self, file:str, lang="en"): 
        # DESCRIPTION: Initialize class, with FPDF's initialization a dataframe is created and cleaned,
        # the group (or chatters) name and a counter are stored, Structure with basic info is built
        
        if not path.exists(file):
            print("No such file exists")
            self.ok = 0
        else:
            self.ok = 1
        
        self.lang = lang

        m = re.search("Chat WhatsApp con (.+?).txt", file) # Catching name of group chat
        if m != None:
            self.name = font_friendly(m.group(1))
        else:
            m = re.search("Chat_WhatsApp_con_(.+?).txt", file)  
            if m != None:   
                self.name = font_friendly(m.group(1))
            else:
                self.name = ""

        if file.endswith(".zip"):
            with ZipFile(file, 'r') as zip_ref:
                m = re.search("WhatsApp Chat - (.+).zip", file)
                self.name = font_friendly(m.group(1)) if m != None else ""
                zip_ref.extractall("text_files")
                file = "text_files/_chat.txt"            

        FPDF.__init__(self) 

        self.counter = 0

        self.df = pd.DataFrame(get_data(file), columns=["date", "time", "who", "message"]) # Creating Dataframe
        self.df.date = pd.to_datetime(self.df.date, format="%d/%m/%y") # Setting dtypes
        self.df.time = pd.to_timedelta(self.df.time)

        self.df = remove_header(self.df) # When people change phone and don't have a backup for their whatsapp messages, 
                                # all of their previous conversations are eliminated, but the "X created this group" message;
                                # when plotting the number of messages per interval, this can create an ugly plot. This function avoids that

        self.group = True
        if len(set(self.df.who)) == 3 and "info" in set(self.df.who): # <- If it's a private chat
            self.group = False # NOT a group chat
            lst = list(set(self.df.who))
            lst.remove("info")
            self.name = tuple([lst[lst.index(self.name)], lst[not lst.index(self.name)]]) # self.group contains name of two chatters
            

        self.plot_pos = {"left":LEFT_PLOT, "right":RIGHT_PLOT} # Used later to format plot into pdf

        self.pos = {"left":0, "right":0} # Variables that keep track where "the pointer" is at, for the left and right sides of the pdf
        self.last = {"left":None, "right":None} # They keep track of the last positioned object

        self.load = (self.pos["left"]/HEIGHT * self.pos["right"]/HEIGHT) * 100 
        #  Defining the progress of the construction of the pdf by getting the position of the pointers relative to the file'sheight 

        prop=FontProperties(fname='../my_fonts/seguiemj.ttf') # Changing matplotib and fpdf font
        rcParams['font.family'] = prop.get_name()
        self.add_font('seguiemj', '', "../my_fonts/seguiemj.ttf")
        self.set_font('seguiemj', '', 16)

        self.add_structure() # Adding the structure of the pdf


    def add_structure(self): # DESCRIPTION: Adding the background of the pdf + aestethics

        self.add_page()

        self.image(PDF_Constructor.img_path+'background.png', x = 0, y = 0, w = WIDTH, h = HEIGHT)
        self.image(PDF_Constructor.img_path+'top_level.png', x = 0, y = 0, w = WIDTH)

        self.cell(15, 0, "")
        self.set_text_color(255, 255, 255)  # Adding top part
        if self.group:
            txt = {"en":f"Analysis of {self.name} chat", 
                   "it":f"Analisi della chat {self.name}"}
            self.multi_cell(WIDTH-70, 0, transform_text(txt[self.lang]))
        else:
            txt = {"en":f"Analysis of {self.name[0]} and {self.name[1]} chat"[:CHAR_PER_LINE], 
                   "it":f"Analisi della chat tra {self.name[0]} e {self.name[1]}"[:CHAR_PER_LINE]}
            self.multi_cell(WIDTH-70, 0, txt[self.lang])
        self.set_text_color(0, 0, 0)

        x, y = self.get_x(), self.get_y()
        self.set_auto_page_break(False)
        self.set_y(-20)

        self.image(PDF_Constructor.img_path+"writing_box.png", x=20, y=self.get_y()-4, w=WIDTH-40) # Adding footer
        self.cell(30, 0)
        self.set_font_size(12)
        txt = {"en":"Do you want to create your own wrapped? 🤨\nThen try it @ http://whatsapp_wrapped.it 👈", 
               "it":"Vuoi creare il wrapped di una tua chat? 🤨\nVai su http://whatsapp_wrapped.it 👈"}

        self.multi_cell(0, 5, txt[self.lang], align="L", link="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
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

        other = "left" if pos == "right" else "right"

        tmp = 100*(((self.pos[pos]+obj_dict[(None, obj)])/HEIGHT)+(self.pos[other]/HEIGHT))
        self.load = tmp if tmp < 100 else 99
        return self.pos[pos]
                


    def add_message(self, cat:str, pos:str) -> None: # DESCRIPTION: add simple info in a similar fashion to a whatsapp message
        # PARAMETERS: cat (str) = type of message to write, available types listed inside of if-else list
        # x, y (int) = coordinates inside of PDF file

        if not self.prep(plot=False):
            return

        # I don't think this is the optimal solution for this find of problem, but it's the best path that I could think of
        # Instead of a long series of if-else conditions or a (not working) dictionary, I decided to use a series of single-use functions
        # The structure of this functions is: 1st) computations, 2nd) creating the text in the correct language

        def message_count(self): # Return number of messages sent in the history of the groupchat
            num = len(self.df) if len(self.df) < 39900 else '40000+'

            txt = {"en":f"{num} messages have been sent!\nYou chat so much 🤩", # Maybe this should be more dynamic...
                   "it":f"Sono stati mandati {num} messaggi!\nVi scrivete un botto! 🤩"} # Especially with not-so-active chats...
            return txt[self.lang]

        def active_days(self): # Return the number of days the chat has been active
            total = len(set(self.df.date))

            txt = {"en":f"This group has benn active in {total} different days! 🧐",
                   "it":f"Vi siete scritti in {total} giorni diversi! 🧐"}
            return txt[self.lang]

        def messages_per_day(self): # Return the number of messages sent every day on average
            message_ratio = len(self.df)/len(pd.date_range(self.df.date[0], date.today())) # <- every day from the start of the groupchat
            message_ratio = round(message_ratio, 2)

            txt = {"en":f"You usually send {message_ratio} messages every day 📱",
                   "it":f"In media vi mandate {message_ratio} messaggi al giorno 📱"}
            return txt[self.lang]

        def file_count(self): # Return the number of files sent
            files = len(self.df[self.df.message == '<Media omessi>'])

            txt = {"en":f"{files} files have been sent in this chatroom!",
                   "it":f"Sono stati inviati {files} file!"}
            return txt[self.lang]

        def most_active_day(self): # Return the day people chatted the most + # of messages sent that day
            num = max([len(self.df[self.df.date == i]) for i in set(self.df.date)])
            day = max(set(self.df.date), key=lambda d: len(self.df[self.df.date == d])).strftime('%d/%m/%y')

            txt = {"en":f"The most active day has been {day}\n{num} total messages, incredible 🤯",
                   "it":f"Il giorno più attivo è stato il {day}\n{num} messaggi in totale, che giornata 🤯"}
            return txt[self.lang]

        def most_active_year(self): # Return the year people chatted the most + # of messages sent that year
            lst = [len(self.df[self.df.date.dt.year == i]) for i in set(self.df.date.dt.year)]
            best, year = max_and_index(lst)
            year = list(set(self.df.date.dt.year))[year]

            txt = {"en":f"Most active year: {year} ({best} messaggi)\nThere were some great memories 💭",
                   "it":f"Anno più attivo: {year} ({best} messaggi)\nChe memorie 💭"}
            return txt[self.lang]

        def most_active_month(self): # Return the month people chatted the most + # of messages sent that month
            lst = [len(self.df[self.df.date.dt.to_period('M').dt.to_timestamp() == i]) for i in set(self.df.date.dt.to_period('M').dt.to_timestamp())]
            best, month = max_and_index(lst)
            month = list(set(self.df.date.dt.to_period('M').dt.to_timestamp()))[month].strftime('%m/%y')

            txt = {"en":f"Most active month: 👇\n{month} ({best} messaggi)",
                   "it":f"Mese più attivo: 👇\n{month} ({best} messaggi)"}
            return txt[self.lang]

        def most_active_weekday(self): # Return the weekday people chatted the most + # of messages sent that weekday
            lst = [len(self.df[self.df.date.dt.day_name() == i]) for i in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]]
            best, weekday = max_and_index(lst)

            txt = {"en":f'Most active weekday: {["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"][weekday]} ({best} messaggi)',
                   "it":f'Giorno più attivo: {["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"][weekday]} ({best} messaggi)'}
            return txt[self.lang]
        
        def most_active_person(self): # Return the name of the most active person in the groupchat + # of messages + percent of total messages
            people = {k:len(self.df[self.df.who == k]) for k in set(self.df.who)}
            person, total = list(sort_dict(people, 1, others=False).items())[0]
            percent = 100*round(total/len(self.df), 2)
            person = font_friendly(person)

            txt = {"en":f"{person} is the most active person!\n They wrote {total} messages ({percent}% of the total) 🤙",
                   "it":f"{person} è la persona più attiva!\n Ha scritto {total} messaggi ({percent}% del totale) 🤙"}
            return txt[self.lang]
        
        def longest_active_streak(self): # Return the start and end dates of the longest streak of days where the chat has been active
            dates = sorted(list(set(self.df.date)))
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
            start, end = start.strftime('%d/%m/%y'), end.strftime('%d/%m/%y')

            txt = {"en":f"Longest active streak: {best_streak} days\nFrom {start} to {end} ❤️",
                   "it":f"Streak di giorni attivi più lunga: {best_streak} giorni\nDal {start} al {end} ❤️"}
            return txt[self.lang]
        
        def longest_inactive_streak(self): # Return the start and end dates of the longest streak of days where the chat has been inactive
            dates = sorted(list(set(self.df.date)))
            start = "01/01/1900"
            end = "01/01/1900"
            best_streak = timedelta(days=1)
            for i in range(1, len(dates)):
                if dates[i]-dates[i-1] > best_streak: # If the gap between days is larger than the previous one
                    start = dates[i-1]                # replace it and reset counter
                    end = dates[i]
                    best_streak = dates[i]-dates[i-1]
            start, end, best_streak = start.strftime('%d/%m/%y'), end.strftime('%d/%m/%y'), best_streak.days

            txt = {"en":f"Longest inactive streak: {best_streak} days\nFrom {start} to {end} ☠️",
                   "it":f"Streak di giorni inattivi più lunga: {best_streak} giorni\nDal {start} al {end} ☠️"}
            return txt[self.lang]
        
        def first_texter(self): # Return the name of the person who text first the most
            people = {}
            for i in range(1, len(self.df)):
                if self.df.date[i] != self.df.date[i-1]: # If first message of the day...
                    who = self.df.who[i]
                    if who not in people:
                        people[who] = 0
                    people[who] += 1
            people = sort_dict(people, 1, others=False, lang=self.lang)
            person = font_friendly(list(people.keys())[0])

            txt = {"en":f"It's usually {person} who writes first... 🥇", 
                   "it":f"Solitamente è {person} che scrive per prim*... 🥇"}
            return txt[self.lang]
        
        def avg_response_time(self): # Return the average time elapsed between a message is sent and a response arrives
            resp_list = []
            date_and_time = self.df.date+self.df.time
            for i in range(1, len(self.df)): # Getting difference between the time of the messages
                resp_list.append(date_and_time[i]-date_and_time[i-1])
            first_quartile, last_quartile = len(self.df)//4, len(self.df)*3//4 # Getting the interquartile mean, since outliers could skew the average too much
            iqr_mean = sum(resp_list[first_quartile:last_quartile], timedelta(0))/len(resp_list)/2
            seconds, minutes, hours, days = (iqr_mean.seconds%60, iqr_mean >= timedelta(minutes=1), iqr_mean >= timedelta(hours=1), iqr_mean >= timedelta(days=1))

            txt = {"en":f"On average a response to a message arrives:\n{f'{iqr_mean.days} days ' if days else ''}{f'{iqr_mean.seconds//3600} hours ' if hours else ''}"
                       +f"{f'{(iqr_mean.seconds//60)%60} minutes ' if minutes else ''}{f'{iqr_mean.seconds%60} seconds'} later 🏃",
                   "it":f"In media un messaggio arriva:\n{f'{iqr_mean.days} giorni ' if days else ''}{f'{iqr_mean.seconds//3600} ore ' if hours else ''}"
                       +f"{f'{(iqr_mean.seconds//60)%60} minuti ' if minutes else ''}{f'{iqr_mean.seconds%60} secondi'} dopo 🏃"}
            return txt[self.lang]

        def swear_count(self): # Returns the total number of swears that have been written in the groupchat
            tot = 0
            words_dict = get_message_freq_dict(self.df.message)
            swears = [i[:-1] for i in open("../lists/parolacce.txt", "r")] # N.B only italian swears for now TODO: add english swears XD
            for swear in swears:
                if swear in words_dict.keys():
                    tot += words_dict[swear]
            
            txt = {"en":f"{tot} swear words have been sent 🤬",
                   "it":f"Sono state dette {txt} parolacce 🤬"}
            return txt[self.lang]
        
        def avg_message_length(self): # Returns the average number of words in a message
            lst = [len(word) for word in [message.split() for message in self.df.message]]
            avg = round(sum(lst)/len(lst), 2)
            
            txt = {"en":f"On average there are {avg} words in a message 🔎",
                   "it":f"Ci sono in media {avg} parole in un messaggio 🔎"}
            return txt[self.lang]

        # TODO: add # of vocals, images and stickers sent (for IOS users only) 
        # TODO: add most active time of day
        # TODO: add most used emoji
            
        possibilities = ["message_count", "active_days", "messages_per_day", "file_count", "most_active_day", "most_active_year", 
                         "most_active_month", "most_active_weekday", "most_active_person", "longest_active_streak", 
                         "longest_inactive_streak", "first_texter", "avg_response_time", "swear_count", "avg_message_length"]
        
        if cat in possibilities:
            txt = eval(cat+"(self)") # Calling the function
        else:
            txt = {"en":"Something went wrong :(",
                   "it":"Qualcosa è andato storto :("}
            txt = txt[self.lang]

        self.set_font_size(11)
        txt_pos = {("right", "one"):GREEN_POS, ("right", "two"):GREEN_POS+1, ("right", "three"):GREEN_POS+1,
                   ("left", "one"):WHITE_POS, ("left", "two"):WHITE_POS-1, ("left", "three"):WHITE_POS-1}
        img_offset = {"right":2, "left":5} # Setting format of message
        pos_to_color = {"left":"white", "right":"green"}

        y = self.update_y(pos, "message", check_text(txt))
   
        self.image(name=PDF_Constructor.img_path+f"{pos_to_color[pos]}_{check_text(txt)}line_bubble.png", # Putting bubble image
                    x=txt_pos[(pos, check_text(txt))]-img_offset[pos], y=y-4, w=100)

        self.set_xy(txt_pos[(pos, check_text(txt))], y)
        self.multi_cell(w=WIDTH/2-5, txt=transform_text(txt), h=5) # Putting text inside bubble


    def plot_emojis(self, pos:str, who:str="", reverse:bool=False, info:bool=True) -> None: 
        # DESCRIPTION: plot most used emojis in chat, place them in PDF given x/y coordinates
        # PARAMETERS: pos ("left"/"right") = position in the pdf | who (str) = if used get emojis of only x character
        # reverse (bool) = if true create barh plot from right to left | info (bool) = add # of emojis to the right of plot
        
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

        emojis = sort_dict(emojis, 7, reverse=reverse, others=False, lang=self.lang)

        if len(emojis.keys()) == 0: # Adding a pair inside the empty dict to avoid crash
            emojis["🏼"] = 0

        title = {"en":"Most used Emojis:", "it":"Emoji più utilizzate:"}
        plt.title(title[self.lang]) # Plotting
        plot = plt.bar(emojis.keys(), emojis.values(), color="#26d367")
        plt.xticks(fontsize=20)
        
        if info:
            txt = {"en":f"{sum(emojis.values())} total\nemojis 😯",
                   "it":f"{sum(emojis.values())} emoji\ntotali 😯"} # Text bubble w/ total number of emoji
            plt.text(x=plt.xlim()[0]+1 if reverse else plt.xlim()[1]-1, y=plt.ylim()[1]*9/10, s=txt[self.lang], 
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

        diff = pd.to_datetime(date.today())-self.df.date[0]
        if ((interval == "month" and diff > timedelta(days=360)) or  # Plot running average if difference of dates
            (interval == "week" and diff > timedelta(days=180)) or   # isn't too small (or else it's useless)
            (interval == "day" and diff > timedelta(days=30))):
            plt.plot(x_pos, running_average, color="#075e55") # Changing format of dates to avoid overlapping
            if pd.to_datetime(x_pos[-1])-pd.to_datetime(x_pos[0]) < timedelta(days=365):
                if pd.to_datetime(x_pos[-1])-pd.to_datetime(x_pos[0]) < timedelta(days=365//2):
                    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
                else:
                    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%y'))
            
        plt.grid(axis="y")
        interval_dict = {"day":{"en":"day", "it":"giorno"}, "week":{"en":"week", "it":"settimana"}, 
                        "month":{"en":"month", "it":"mese"}, "year":{"en":"year", "it":"anno"}}
        title = {"en":f"Number of messages per {interval_dict[interval][self.lang]}",
                 "it":f"Numero di messaggi per {interval_dict[interval][self.lang]}"}
        plt.title(title[self.lang])
        
        plt.savefig(str(self.counter), transparent=True)
        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))
    

    def plot_day_of_the_week(self, pos:str) -> None: # DESCRIPTION: Plotting number of messages sent per weekday
        # PARAMETERS: pos ("left"/"right") = position in the pdf

        if not self.prep():
            return

        weekday = {"en":["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                   "it":["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]}
        y_pos = [len(self.df[self.df.date.dt.day_name() == i]) for i in weekday["en"]]

        spider_plot(weekday[self.lang], y_pos)
        title = {"en":"Number of messages per weekday:",
                 "it":"Numero di messaggi per giorno della settimana:"}
        plt.title(title[self.lang], pad=30)
        plt.savefig(str(self.counter), transparent=True)
        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))
                
    

    def plot_most_used_words(self, pos:str, wordcloud:bool=True) -> None: # DESCRIPTION: Barplot with most used words
        # PARAMETERS: pos ("left"/"right") = position in the pdf | wordcloud (bool) = use barplot or wordcloud

        if not self.prep():
            return
        
        blacklist = [i[:-1] for i in open("../lists/blacklist.txt", "r").readlines()] + ["è"] # Used to get rid of boring words (articles, prepositions...)
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
        
        title = {"en":"Most used words:", 
                 "it":"Parole più utilizzate:"}
        plt.title(title[self.lang])
        plt.savefig(str(self.counter), transparent=True)
        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))
    

    def plot_most_active_people(self, pos:str) -> None: # DESCRIPTION: Plot most number of messages sent per person
        # PARAMETERS: pos ("left"/"right") = position in the pdf

        if not self.prep():
            return

        people = {font_friendly(k):len(self.df[self.df.who == k]) for k in set(self.df.who)} # Dict {person:number of messages}
        if "info" in people.keys():
            people.pop("info")
        people = sort_dict(people, 7, reverse=True, lang=self.lang)
        
        if self.group: # If group chat use barplot
            title = {"en":f"Most active people in {self.name}", 
                     "it":f"Persone più attive in {self.name}:"}
            plt.title(title[self.lang])
            set_to_font_size = {1:150, 2:45, 3:40, 4:35, 5:32, 6:25, 7:21, 8:18, 9:15, 10:14} # Different sizes of people create different graphs
            plot = plt.barh([str(i) for i in people.values()], people.values(), color="#26d367")
            add_labels_to_bar(plot, people.keys(), font_size=set_to_font_size[len(people)], dir="horizontal", pos="internal")

        else: # If private chat use pie plot
            title = {"en":"Number of messages:", # Better title?
                     "it":"Numero di messaggi inviati:"}
            plt.title(title[self.lang])
            plt.pie(x=people.values(), labels=people.keys(), colors=("#26d367", "#128c7f"), textprops={"fontsize":14},
                    autopct=lambda x: f"{int(round((x/100)*sum(people.values()), 0))} messaggi\n({round(x, 2)}%)")

        plt.savefig(str(self.counter), transparent=True)
        self.add_image(self.plot_pos[pos], self.update_y(pos, "plot"))


    def plot_time_of_messages(self, pos:str): # DESCRIPTION: Plot number of messages per time period
        # PARAMETERS: pos ("left"/"right") = position in the pdf

        if not self.prep():
            return

        title = {"en":"Number of messages per time of day:",
                  "it":"Numero di messaggio per periodo del giorno:"}
        plt.title(title[self.lang])

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
    
    
    def save(self) -> str: # DESCRIPTION: Save file if nothing has gone wrong, remove images created
        if not self.prep(plot=False):
            return

        self.load = 100
        out = {"en":f"Analysis of {self.name if self.group else f'{self.name[0]} and {self.name[1]}'} chat.pdf",
               "it":f"Analisi della chat {self.name if self.group else f'tra {self.name[0]} e {self.name[1]}'}.pdf"}
        out = out[self.lang]
        self.output(name=f'{out}')
        move(f'{out}', f'../pdfs/{out}')
        while self.counter != 0:
            if path.exists(f"{self.counter}.png"):
                remove(f"{self.counter}.png")
            self.counter -= 1
        
        possibilities = [f"Chat WhatsApp con {self.name if type(self.name) != tuple else self.name[0]}.txt",
                         f"Chat WhatsApp_con_{self.name if type(self.name) != tuple else self.name[0]}.txt",
                         f"WhatsApp Chat - {self.name if type(self.name) != tuple else self.name[0]}.zip",
                         f"WhatsApp_Chat_-_{self.name if type(self.name) != tuple else self.name[0]}.zip",
                         f"_chat.txt"]
        for i in possibilities:
            if path.exists(f"text_files/{i}"):
                remove(f"text_files/{i}")
        
        return f'../pdfs/{out}'