import datetime
from datetime import date
import calendar

date_list = []
a_dict = {}

curr_day = '2022-04-23'
xls_row = 541
start_date = date.fromisoformat(curr_day)
# print(f'start_date {start_date}')

day_name = calendar.day_name[date.fromisoformat(curr_day).weekday()]
# print(f'day_name {day_name}')
number_of_days = 253

## this for loop is generate the next 31 dates in list format
for day in range(number_of_days):
  a_date = (start_date + datetime.timedelta(days = day)).isoformat()
  print(f'a_date {a_date}, day {day}')
  date_list.append(a_date)
# print(date_list)



for dt in date_list:    
    if (calendar.day_name[date.fromisoformat(dt).weekday()]) == 'Monday' :
      # print(f'day = {calendar.day_name[date.fromisoformat(dt).weekday()]}')
      # print(dt)      
      xls_row +=2
      # print(f'{dt} {xls_row}')
      # print(f'day = {calendar.day_name[date.fromisoformat(dt).weekday()]} date = {dt} {xls_row}')
    else:
      xls_row +=1
      # print(f'day = {calendar.day_name[date.fromisoformat(dt).weekday()]} date = {dt} {xls_row}')
    
    a_dict[dt] = xls_row

for i in a_dict.items():
  print(i)