from django.core.mail import send_mail
from datetime import datetime
import os
from django.contrib.auth.models import User
from models import MealPlan

def daily_emails():
  print("executed daily!")
  cur_datetime = datetime.now()
  cur_day = cur_datetime.day
  cur_month = cur_datetime.month
  subject = f"Daily Meal Plan: {cur_month}/{cur_day}"
  sender = 'notifications@souschef.life'

  mealplan_users = User.objects.all().filter(meal_plans__isnull=False)
  for user in mealplan_users:
    plan = user.meal_plans.first()
    breakfast = user.meal_plans
    recipient = user.email
    message = 'Hello, username!\nHere is your meal plan for the day:\n'



  print(subject)
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
