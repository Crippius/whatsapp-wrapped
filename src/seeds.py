# Here are some seeds that can be used to create PDF
# obviously since 

from random import randint

import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
utilities_dir = current_dir.parent / 'src'
sys.path.append(str(utilities_dir.parent))

from src.pdf.constructor import PDF_Constructor 

def seed1(pdf:PDF_Constructor): # One possible combination of plot and messages (for group chats)
    
    pdf.add_number_of_messages_plot(interval="day", pos="left")

    pdf.add_message(cat="most_active_day", pos="left")

    pdf.add_emoji_plot(pos="left")

    pdf.add_most_active_people_plot(pos="left")

    pdf.add_message(cat="message_count", pos="right")

    pdf.add_time_of_messages_plot(pos="right")

    pdf.add_message(cat="longest_active_streak", pos="right")

    pdf.add_message(cat="longest_inactive_streak", pos="right")

    pdf.add_most_used_words_plot(pos="right", wordcloud=True)

    pdf.add_message(cat="avg_response_time", pos="right")


def seed2(pdf:PDF_Constructor): # Another possible combination (Made exclusively for private chats)

    pdf.add_emoji_plot("left", who=pdf.name[0])

    pdf.add_emoji_plot("right", who=pdf.name[1], reverse=True)

    pdf.add_number_of_messages_plot("left")

    pdf.add_time_of_messages_plot("right")

    pdf.add_most_active_people_plot("left")


def seed3(pdf:PDF_Constructor):

    pdf.add_number_of_messages_plot(interval="month", pos="left")

    pdf.add_message(cat="most_active_month", pos="left")

    pdf.add_most_used_words_plot(pos="left")

    pdf.add_message(cat="avg_message_length", pos="left")

    pdf.add_message(cat="avg_response_time", pos="left")

    pdf.add_message(cat="most_active_person", pos="right")

    pdf.add_most_active_people_plot(pos="right")

    pdf.add_message(cat="first_texter", pos="right")

    pdf.add_emoji_plot(pos="right")

    pdf.add_message(cat="active_days", pos="right")


def main():
    
    file = "../text_files/Chat WhatsApp con ESEMPIO.txt"

    pdf = PDF_Constructor(file, lang="it")

    eval(f"seed{1}(pdf)")

    pdf.save()

if __name__ == "__main__":

    main()


