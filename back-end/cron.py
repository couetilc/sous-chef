from django.core.mail import send_mail
from datetime import datetime
import os
from django.contrib.auth.models import User
from api.models import MealPlan

def daily_emails():
  print("executed daily!")
  cur_datetime = datetime.now()
  cur_day = cur_datetime.day
  cur_day_ofweek = cur_datetime.weekday()
  cur_month = cur_datetime.month
  subject = f"Daily Meal Plan: {cur_month}/{cur_day}"
  sender = 'notifications@souschef.life'

  mealplan_users = User.objects.all().filter(meal_plans__isnull=False)
  for user in mealplan_users:
    plan = user.meal_plans.first()
    recipient = user.email
    message = f'Hello, {user.username}!\nHere is your meal plan for the day:\n'

    meals = plan.get_meals_for_day(cur_day_ofweek)
    breakfast_servings = meals[0].servings
    lunch_servings = meals[1].servings
    dinner_servings= meals[2].servings
    breakfast = meals[0].recipe
    lunch = meals[1].recipe
    dinner = meals[2].recipe
    # breakfast nutrition
    breakfast_cals = breakfast.calories_per_serving * breakfast_servings
    breakfast_fat = breakfast.fat_g * breakfast_servings
    breakfast_carbs = breakfast.carbs_g * breakfast_servings
    breakfast_protein = breakfast.protein_g * breakfast_servings
    # lunch nutrition
    lunch_cals = lunch.calories_per_serving * lunch_servings
    lunch_fat = lunch.fat_g * lunch_servings
    lunch_carbs = lunch.carbs_g * lunch_servings
    lunch_protein = lunch.protein_g * lunch_servings
    # dinner nutrition
    dinner_cals = dinner.calories_per_serving * dinner_servings
    dinner_fat = dinner.fat_g * dinner_servings
    dinner_carbs = dinner.carbs_g * dinner_servings
    dinner_protein = dinner.protein_g * dinner_servings

    # breakfast 
    message += '\nBreakfast:\n'
    message += breakfast.title + '\n'
    #need to display this as a link, not a url
    message += breakfast.image_url + '\n'
    message += '\nBreakfast Nutrition:\n'
    message += f'Calories: {breakfast_cals} kCals\n'
    message += f'Fat: {breakfast_fat} grams\n'
    message += f'Carbs: {breakfast_carbs} grams\n'
    message += f'Protein: {breakfast_protein} grams\n\n'

    # lunch
    message += '\nLunch:\n'
    message += lunch.title + '\n'
    #need to display this as a link, not a url
    message += lunch.image_url + '\n'
    message += '\nLunch Nutrition:\n'
    message += f'Calories: {lunch_cals}\n kCals'
    message += f'Fat: {lunch_fat} grams\n'
    message += f'Carbs: {lunch_carbs} grams\n'
    message += f'Protein: {lunch_protein} grams\n\n'

    # dinner
    message += '\nDinner:\n'
    message += dinner.title + '\n'
    #need to display this as a link, not a url
    message += dinner.image_url + '\n'
    message += '\nDinner Nutrition:\n'
    message += f'Calories: {dinner_cals} kCals\n'
    message += f'Fat: {dinner_fat} grams\n'
    message += f'Carbs: {dinner_carbs} grams\n'
    message += f'Protein: {dinner_protein} grams\n'
    
    message += '\nThank you for using SousChef!\nVisit our website at souschef.life\n'
    send_mail(subject, message, sender, [recipient])

def weekly_emails():
  print("executed weekly!")
  cur_datetime = datetime.now()
  cur_day = cur_datetime.day
  cur_day_ofweek = cur_datetime.weekday()
  cur_month = cur_datetime.month
  subject = f"Daily Meal Plan: {cur_month}/{cur_day}"
  sender = 'notifications@souschef.life'

  mealplan_users = User.objects.all().filter(meal_plans__isnull=False)
  for user in mealplan_users:
    recipient = user.email
    # Part 1:
    # api call to get every active user's meal plan for this week
    # format it
    # use send_mail to send it
    # Part 2:
    # api call to get every active user's meal plan for next week
    # format it
    # use send_mail to send it
    message += 'Thank you for using SousChef!\nVisit our website at souschef.life\n'
    send_mail(subject, message, sender, [recipient])

def weekly_grocery_emails():
  print('sent grocery lists!')
  cur_datetime = datetime.now()
  cur_day = cur_datetime.day
  cur_day_ofweek = cur_datetime.weekday()
  cur_month = cur_datetime.month
  subject = f"Daily Meal Plan: {cur_month}/{cur_day}"
  sender = 'notifications@souschef.life'

  mealplan_users = User.objects.all().filter(meal_plans__isnull=False)
  for user in mealplan_users:
    recipient = user.email
    # part 1:
    # iterate over active users {
    #   api call get diff between NEXT WEEK's meal plan ingredients and inventory ingredients
    #   format info
    #   use send mail to send it
    # }
    message += 'Thank you for using SousChef!\nVisit our website at souschef.life\n'
    send_mail(subject, message, sender, [recipient])
