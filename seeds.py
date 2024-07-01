# Here are some seeds that can be used to create PDF
# obviously since 

from random import randint
from PDF_Constructor import PDF_Constructor

def seed1(pdf:PDF_Constructor): # One possible combination of plot and messages (for group chats)
    
    pdf.plot_number_of_messages(interval="day", pos="left")

    pdf.add_message(cat="most_active_day", pos="left")

    pdf.plot_emojis(pos="left")

    pdf.plot_most_active_people(pos="left")

    pdf.add_message(cat="message_count", pos="right")

    pdf.plot_time_of_messages(pos="right")

    pdf.add_message(cat="longest_active_streak", pos="right")

    pdf.add_message(cat="longest_inactive_streak", pos="right")

    pdf.plot_most_used_words(pos="right", wordcloud=True)

    pdf.add_message(cat="avg_response_time", pos="right")


def seed2(pdf:PDF_Constructor): # Another possible combination (Made exclusively for private chats)

    pdf.plot_emojis("left", who=pdf.name[0])

    pdf.plot_emojis("right", who=pdf.name[1], reverse=True)

    pdf.plot_number_of_messages("left")

    pdf.plot_time_of_messages("right")

    pdf.plot_most_active_people("left")


def seed3(pdf:PDF_Constructor):

    pdf.plot_number_of_messages(interval="month", pos="left")

    pdf.add_message(cat="most_active_month", pos="left")

    pdf.plot_most_used_words(pos="left")

    pdf.add_message(cat="avg_message_length", pos="left")

    pdf.add_message(cat="avg_response_time", pos="left")

    pdf.add_message(cat="most_active_person", pos="right")

    pdf.plot_most_active_people(pos="right")

    pdf.add_message(cat="first_texter", pos="right")

    pdf.plot_emojis(pos="right")

    pdf.add_message(cat="active_days", pos="right")


def main():
    
    file = "text_files/Chat WhatsApp con Matthew.txt"

    pdf = PDF_Constructor(file, lang="it")

    eval(f"seed{1}(pdf)")

    pdf.save()

if __name__ == "__main__":

    main()


