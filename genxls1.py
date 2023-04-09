import datetime
from datetime import date
import calendar

## Note : Only increase the number_of_days to next 30days

curr_day = '2022-01-31'
xls_row = 449
a_dict = {}
date_list = []

start_date = date.fromisoformat(curr_day)

day_name = calendar.day_name[date.fromisoformat(curr_day).weekday()]
number_of_days = 100

for day in range(number_of_days):
  a_date = (start_date + datetime.timedelta(days = day)).isoformat()
  date_list.append(a_date)

# print(date_list)

for variable in date_list:
    if (calendar.day_name[date.fromisoformat(variable).weekday()]) == 'Sunday' :
      print(f'{variable}: {xls_row}')
      xls_row +=2
    else:
      print(f'{variable}: {xls_row}')
      # if xls_row == 449:
      #   xls_row=450
      xls_row +=1
    # print(a_dict)
    a_dict[variable] = xls_row


#

# for i in a_dict.items():
#   print(i)


