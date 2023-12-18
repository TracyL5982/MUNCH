from flask_mail import Message
import random

icebreaker_questions = [
    "If you could have dinner with any historical figure, who would it be and why?",
    "What's one book you think everyone should read?",
    "If you could visit any place in the world, where would it be and why?",
    "What's your favorite hobby or activity to do in your free time?",
    "What's one skill you'd like to learn or improve this year?",
    "If you could only eat one food for the rest of your life, what would it be?",
    "What's the most interesting fact you know?",
    "If you could have any superpower, what would it be and why?",
    "What was your favorite subject in school?",
    "If you could be any animal for a day, which would you choose and why?",
    "What's the best piece of advice you've ever received?",
    "What's one movie that you can watch over and over again?",
    "If you were stranded on a deserted island, what three items would you want to have with you?",
    "What's your favorite season of the year and why?",
    "What's a talent or skill you wish you had?",
    "If you could switch lives with anyone for a day, who would it be and why?",
    "What's the most spontaneous thing you've ever done?",
    "What's a goal you've set for yourself recently?",
    "If you could speak another language fluently, which would it be?",
    "What's something you're looking forward to in the near future?"
]

def send_match_notification(mail, match, classroom_name):
   emails = []
   emails.append(match["user1_email"])
   emails.append(match["user2_email"])
   if "user3_id" in match:
      emails.append(match["user3_email"])
   msg = Message("Classroom " + classroom_name.capitalize() + ": Match Notification!", sender = 'munchyale@gmail.com', recipients = emails)
   match_message = ""
   if "user3_id" in match:
      match_message = match["user1_name"].capitalize() + ", " + match["user2_name"].capitalize() + ", and " + match["user3_name"].capitalize()
   else:
      match_message = match["user1_name"].capitalize() + " and " + match["user2_name"].capitalize()
   body = "Hello " + match_message + "!\nYou've been matched for " + classroom_name.capitalize() + " classroom's lunchtag. "
   body += "Here's a question to break the ice: "
   body += random.choice(icebreaker_questions)
   body += " Include your answer in your reply to this email when scheduling your meal!"
   msg.body = body
   mail.send(msg)
   return "Sent"

def send_daily_reminder(mail, emails, classroom_name):
   subject = classroom_name.capitalize() + " classroom's Munch Reminder!"
   msg = Message(subject, sender= 'munchyale@gmail.com', recipients = emails)
   msg.body = "This is your daily reminder to do lunchtag!"
   mail.send(msg)
   return "Sent"
