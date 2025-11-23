from django.core.mail import send_mail
import datetime

def daily_emails():
  print("executed daily!")
  today_date = datetime.date.today()
  subject = 'Daily Meal Plan: today_date.strftime("%d-%m-%Y")'
  print(subject)
  message = 'Hello, username!\nHere is your meal plan for the day:\n'
  sender = 'notifications@souschef.life'
  recipient = 'test@test.com'
  send_mail(subject, message, sender, [recipient])
  # api call to get evry active user's mael plan info for today
  # format it
  # use send_mail to send it
  

def weekly_emails():
  print("executed weekly!")
  # Part 1:
  # api call to get every active user's meal plan for this week
  # format it
  # use send_mail to send it
  # Part 2:
  # api call to get every active user's meal plan for next week
  # format it
  # use send_mail to send it

def weekly_grocery_emails():
  print('sent grocery lists!')
  # part 1:
  # iterate over active users {
  #   api call get diff between NEXT WEEK's meal plan ingredients and inventory ingredients
  #   format info
  #   use send mail to send it
  # }
