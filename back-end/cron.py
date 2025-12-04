from django.core.mail import send_mail
from datetime import datetime, timedelta
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
    message = f'Hello, {user.username}! Here is your meal plan for the day:\n'
    html_message = f'<p>Hello, {user.username}!</p><p>Here is your meal plan for the day:<p>'
    

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
    message += 'Breakfast:'
    html_message += '<h1>\nBreakfast:</h1>'
    message += breakfast.title + '\n'
    html_message += f'<p>{breakfast.title}</p>'
    #need to display this as a link, not a url
    message += breakfast.image_url + '\n'
    html_message += f'<img src={breakfast.image_url}\n/>'
    message += '\nBreakfast Nutrition:\n'
    html_message += '<p>\nBreakfast Nutrition:\n</p>'
    message += f'Calories: {breakfast_cals} kCals\n'
    html_message += f'<p>Calories: {breakfast_cals} kCals</p>'
    message += f'Fat: {breakfast_fat} grams\n'
    html_message += f'<p>Fat: {breakfast_fat} grams</p>'
    message += f'Carbs: {breakfast_carbs} grams\n'
    html_message += f'<p>Carbs: {breakfast_carbs} grams</p>'
    message += f'Protein: {breakfast_protein} grams\n\n'
    html_message += f'<p>Protein: {breakfast_protein} grams\n</p>'

    # lunch
    html_message += '<h1>\nLunch:\n</h1>'
    message += lunch.title + '\n'
    html_message += f'<p>{lunch.title}</p>'
    #need to display this as a link, not a url
    message += lunch.image_url + '\n'
    html_message += f'<img src={lunch.image_url}/>'
    message += '\nLunch Nutrition:\n'
    html_message += '<p>\nBreakfast Nutrition:</p>'
    message += f'Calories: {lunch_cals} kCals\n'
    html_message += f'<p>Calories: {lunch_cals} kCals</p>'
    message += f'Fat: {lunch_fat} grams\n'
    html_message += f'<p>Fat: {lunch_fat} grams</p>'
    message += f'Carbs: {lunch_carbs} grams\n'
    html_message += f'<p>Carbs: {lunch_carbs} grams</p>'
    message += f'Protein: {lunch_protein} grams\n\n'
    html_message += f'<p>Protein: {lunch_protein} grams\n</p>'

    # dinner

    html_message += '<h1>\nDinner:\n</h1>'
    message += dinner.title + '\n'
    html_message += f'<p>{dinner.title}</p>'
    #need to display this as a link, not a url
    message += dinner.image_url + '\n'
    html_message += f'<img src={dinner.image_url}\n/>'
    message += '\nDinner Nutrition:\n'
    html_message += '<p>\nBreakfast Nutrition:</p>'
    message += f'Calories: {dinner_cals} kCals\n'
    html_message += f'<p>Calories: {dinner_cals} kCals</p>'
    message += f'Fat: {dinner_fat} grams\n'
    html_message += f'<p>Fat: {dinner_fat} grams\n</p>'
    message += f'Carbs: {dinner_carbs} grams\n'
    html_message += f'<p>Carbs: {dinner_carbs} grams</p>'
    message += f'Protein: {dinner_protein} grams\n\n'
    html_message += f'<p>Protein: {dinner_protein} grams</p>'

    message += '\nThank you for using SousChef!\nVisit our website at souschef.life\n</p>'
    html_message += '<p>\nThank you for using SousChef!\nVisit our website at <a href="www.souschef.life">souschef.life</a><p>'
    html_message = f'<html>\n<body>\n{html_message}\n</body>\n</html>'
    send_mail(subject, message, sender, [recipient], fail_silently=True, html_message=html_message)


def weekly_emails():
  print("executed weekly!")
  weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  cur_datetime = datetime.now()
  cur_day = cur_datetime.day
  days_til_mond = (0 - cur_datetime.weekday() + 7) % 7
  if days_til_mond == 0:
    days_til_mond = 7

  next_mond = cur_datetime + timedelta(days=days_til_mond)
  mond_month = next_mond.month
  mond_day = next_mond.day
  next_sund = next_mond + timedelta(days=6)
  sund_month = next_sund.month
  sund_day = next_sund.day
  subject = f"This Week's Meal Plan: {mond_month}/{mond_day} to {sund_month}/{sund_day}"
  sender = 'notifications@souschef.life'

  mealplan_users = User.objects.all().filter(meal_plans__isnull=False)
  for user in mealplan_users:
    recipient = user.email
    message = f'Hello, {user.username}! Here is your meal plan for next week: {mond_day}-{sund_month}/{sund_day}\n'
    plan = user.meal_plans.filter(week_start=next_mond).first()
    # only send weekly plan email if user has a plan for next week
    if not plan:
      continue
    
    # iterate over all days from next_mond to next_sund
    for i in range(7):
      day = next_mond + timedelta(days=i)
      message += f'\n{weekdays[i]}: {day.month}/{day.day}\n'

      meals = plan.get_meals_for_day(day.weekday())
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
      message += 'Breakfast:\n'
      message += breakfast.title + '\n'
      message += '\nBreakfast Nutrition:\n'
      message += f'Calories: {breakfast_cals} kCals\n'
      message += f'Fat: {breakfast_fat} grams\n'
      message += f'Carbs: {breakfast_carbs} grams\n'
      message += f'Protein: {breakfast_protein} grams\n\n'

      # lunch
      message += 'Lunch:\n'
      message += lunch.title + '\n'
      message += '\nLunch Nutrition:\n'
      message += f'Calories: {lunch_cals} kCals\n'
      message += f'Fat: {lunch_fat} grams\n'
      message += f'Carbs: {lunch_carbs} grams\n'
      message += f'Protein: {lunch_protein} grams\n\n'

      # dinner

      message += 'Dinner:\n'
      message += dinner.title + '\n'
      message += '\nDinner Nutrition:\n'
      message += f'Calories: {dinner_cals} kCals\n'
      message += f'Fat: {dinner_fat} grams\n'
      message += f'Carbs: {dinner_carbs} grams\n'
      message += f'Protein: {dinner_protein} grams\n\n'



    # Part 1:
    # api call to get every active user's meal plan for this week
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
    # iterate over active users {
    #   api call get next week's meal plan
    #   api call get shopping list for next week
    #   format info
    #   use send mail to send it
    # }
    message += 'Thank you for using SousChef!\nVisit our website at souschef.life\n'
    send_mail(subject, message, sender, [recipient])
