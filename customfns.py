from __future__ import print_function

import datetime
import json,sys
import time
from json import JSONDecodeError
import requests
import certifi
import isengard
import xlrd
from <redacted>
from mapexcel import MAP_DATE_XLS 
from  constants import *
from  prilistdate import pri


# Auth
<redacted internal authentication process>

SUB_DICT ={}
# Webhook download
S3_CLIENT.download_file(S3_BUCKET, URI_FILE, URL_LOCAL_FILE)

# Primary roster list download
# S3_CLIENT.download_file('ams-ops-iad-roster-list', 'list.txt', '/tmp/list.txt')
# Created Bucket 
S3_CLIENT.download_file(S3_BUCKET, 'list.txt', LISTFILE)
# S3_CLIENT.download_file(S3_BUCKET, 'nex_day_log_file_url.txt', NEXT_DAY_LOCAL_FILE_URL)

# Download and open schedule spreadsheet
# Filename = 'IAD_SEA_2021-Schedule-Till-Aug-2021.xlsx'

# Filename = 'IAD_SEA_2022-Schedule.xlsx'
Filename = 'IAD_DFW_SEA_2022-Schedule.xlsx'

FilePath = "/home/alekhyal/Roaster-IAD-DFW/" + ENV + "/" + Filename
S3_CLIENT.download_file(S3_BUCKET, Filename, FilePath)
SCHEDULE_LOCATION = FilePath
#FilePath
#"/home/alekhyal/Roaster-IAD-DFW/Testing/IAD_DFW_SEA_2022-Schedule_real.xlsx"
EXCEPTION = [<redacted>]
EPSLIST = [<redacted>]
PATCHLIST = [<redacted>]
WB = xlrd.open_workbook(SCHEDULE_LOCATION)
SHEET = WB.sheet_by_index(0)

# main code to get assignments
def get_next_day_assignments():
    """
    This method will POST IAD Ops On Call schedule for the immediate next day using Chime Webhook
    """
    day_start = 2
    # the day I want to start from - today's date
    day_end = 20
    # day_end - day_start = number of days I want the schedule to be made for
    date_primaries = {} 
    pri_list = []
    date_list = []
    sub_dict={}
    for value in range(day_start, day_end):
        next_date = datetime.date.today() + datetime.timedelta(days=value)
        nx_dt=next_date.strftime("%m-%d-%Y")
        # print(nx_dt)
        day_of_week = next_date.strftime(" %A")
        
        ## from oncall calendar page pull the details of primaries
        on_call_list = get_primaries_list(value)
        index = 1
        schedule_next_day = ""
        prev_primary = ""
        on_call = get_engineer_spreadsheet(str(next_date))     # people working on the day from spredsheet   
        daily_primaries = []
        # Finding appropriate AD admins for the day
        ad_help = []
        for ad_helper in AD_ADMINS:
            if ad_helper in on_call:
                ad_help.append('@' + ad_helper)
        ad_str = ', '.join(ad_help)

        print("\nIAD schedule for " + str(next_date) + day_of_week + " Take 1 - \n")
        # logging.INFO(f'IAD schedule for {str(next_date)} {day_of_week} Take 1 - ')

        for oncall_team in TEAM_ALIAS:
            url = "<redacted" + str(next_date)
            ##logging.INFO(url)
            # print(url)     
            response = requests.get(url, headers=ONCALL_HEADERS, auth=AUTH)
            ##logging.INFO(response)
            try:
                """
                Logic - 
                1. Get oncall engineer from ON Call calendar
                2. Verify if engineer is working for the day; if yes then append engineer to day roster
                3. If not, then find new primary using ordered list
                Example - 'a' is primary as per on call, however 'a' has day off.
                ordered_list = ['c', 'b', 'a', 'e', 'd']
                Pick 'c' and check if 'c' is working; if yes, then 'c' gets picked as primary. 
                The order of the list will be -  ['b', 'a', 'e', 'd', 'c'] - look how 'c' moved to last
                position here. 
                If 'c' is not working, then move to next element in the list and so on. 
                4. New primary is picked and is appended to daily roster
                """
                if oncall_team == 'aws-ams-ops-oncall':
                    primary = get_primary_from_oncall(next_date, oncall_team) # directly picked from oncall portal
                    time.sleep(0.5)
                    if primary not in on_call: # on_call = Abhis scheduele, ppl working today
                        if primary is None:
                            primary = find_new_primary(primary, on_call_list, index,value, on_call)[0]
                            on_call_list = find_new_primary(primary, on_call_list, index,value, on_call)[1]
                            # for patch create new func
                            time.sleep(0.5)
                            daily_primaries.append(primary)
                            date_primaries[ONCALL_TEAM_DICT[oncall_team]] = primary
                            # phase 1
                            pri_list.append(date_primaries)
                            upload_to_on_call(primary, oncall_team, OPS_PRIM_ROT_ID, day_start)
                        prev_primary += ONCALL_TEAM_DICT[oncall_team] + primary + " \n"
                        primary = find_new_primary(primary, on_call_list, index,value, on_call)[0]
                        on_call_list = find_new_primary(primary, on_call_list, index,value, on_call)[1]
                        time.sleep(1)
                        daily_primaries.append(primary)
                        date_primaries[ONCALL_TEAM_DICT[oncall_team]] = primary
                        pri_list.append(date_primaries)
                        upload_to_on_call(primary, oncall_team, OPS_PRIM_ROT_ID, day_start)
                    else:
                        date_primaries[ONCALL_TEAM_DICT[oncall_team]] = primary
                        pri_list.append(date_primaries)
                        daily_primaries.append(primary)
                elif oncall_team == 'aws-ams-ops-eps':
                    primary = get_primary_from_oncall(next_date, oncall_team)
                    time.sleep(0.5)
                    if primary not in on_call:
                        if primary is None:
                            primary = find_new_eps_primary(primary, on_call_list, index,value, on_call)[0]
                            on_call_list = find_new_eps_primary(primary, on_call_list, index,value, on_call)[1]
                            daily_primaries.append(primary)
                            time.sleep(1)
                            date_primaries[ONCALL_TEAM_DICT[oncall_team]] = primary
                            upload_to_on_call(primary, oncall_team, EPS_ROT_ID,day_start)
                        prev_primary += ONCALL_TEAM_DICT[oncall_team] + primary + " \n"
                        primary = find_new_eps_primary(primary, on_call_list, index,value, on_call)[0]
                        on_call_list = find_new_patch_primary(primary, on_call_list, index,value, on_call)[1]
                        time.sleep(1)
                        date_primaries[ONCALL_TEAM_DICT[oncall_team]] = primary
                        pri_list.append(date_primaries)
                        pri_list.append(date_primaries)
                        upload_to_on_call(primary, oncall_team, EPS_ROT_ID, day_start)
                    else:
                        date_primaries[ONCALL_TEAM_DICT[oncall_team]] = primary
                        pri_list.append(date_primaries)
                        daily_primaries.append(primary)
                elif oncall_team == 'aws-ams-patch-oncall':
                    primary = get_primary_from_oncall(next_date, oncall_team)
                    time.sleep(0.5)
                    if primary not in on_call:
                        if primary is None:
                            primary = find_new_patch_primary(primary, on_call_list, index,value, on_call)[0]
                            on_call_list = find_new_patch_primary(primary, on_call_list, index,value, on_call)[1]
                            daily_primaries.append(primary)
                            time.sleep(1)
                            date_primaries[ONCALL_TEAM_DICT[oncall_team]] = primary
                            upload_to_on_call(primary, oncall_team, PATCH_ROT_ID,day_start)
                        prev_primary += ONCALL_TEAM_DICT[oncall_team] + primary + " \n"
                        primary = find_new_patch_primary(primary, on_call_list, index,value, on_call)[0]
                        on_call_list = find_new_patch_primary(primary, on_call_list, index,value, on_call)[1]
                        time.sleep(1)
                        date_primaries[ONCALL_TEAM_DICT[oncall_team]] = primary
                        pri_list.append(date_primaries)
                        pri_list.append(date_primaries)
                        upload_to_on_call(primary, oncall_team, PATCH_ROT_ID, day_start)
                    else:
                        date_primaries[ONCALL_TEAM_DICT[oncall_team]] = primary
                        pri_list.append(date_primaries)
                        daily_primaries.append(primary)
                elif oncall_team == 'aws-ams-sr-primary':
                    primary = get_primary_from_oncall(next_date, oncall_team)
                    time.sleep(0.5)
                    if primary not in on_call:
                        if primary is None:
                            primary = find_new_primary(primary, on_call_list, index,value, on_call)[0]
                            on_call_list = find_new_primary(primary, on_call_list, index,value, on_call)[1]
                            daily_primaries.append(primary)
                            time.sleep(1)
                            date_primaries[ONCALL_TEAM_DICT[oncall_team]] = primary
                            upload_to_on_call(primary, oncall_team, SR_ROT_ID,day_start)
                        prev_primary += ONCALL_TEAM_DICT[oncall_team] + primary + "\n"
                        primary = find_new_primary(primary, on_call_list, index,value, on_call)[0]
                        on_call_list = find_new_primary(primary, on_call_list, index,value, on_call)[1]
                        daily_primaries.append(primary)
                        time.sleep(1)
                        date_primaries[ONCALL_TEAM_DICT[oncall_team]] = primary
                        pri_list.append(date_primaries)
                        upload_to_on_call(primary, oncall_team, SR_ROT_ID,day_start)
                    else:
                        date_primaries[ONCALL_TEAM_DICT[oncall_team]] = primary
                        pri_list.append(date_primaries)
                        daily_primaries.append(primary)
                elif oncall_team == 'aws-ams-patch1-oncall':
                    primary = get_primary_from_oncall(next_date, oncall_team)
                    time.sleep(0.5)
                    if primary is None:
                        primary = ' no PP '
                    if primary not in on_call:
                        primary = primary + ' has day off. Need a patcher!!'
                elif oncall_team == 'aws-ams-csdm-on-call':
                    # print(response.json())
                    try:
                        primary = response.json()[0]['oncallMember'][0]
                    except:
                        primary = ' no CSDM on call calendar '
                    time.sleep(0.5)
                elif oncall_team == 'aws-ams-security':
                    primary = get_security(next_date)
                    time.sleep(0.5)
                elif oncall_team == 'aws-ams-ops-eps1':
                    primary = get_primary_from_oncall(next_date, oncall_team)
                    # print("EPS prim", primary)
                    time.sleep(0.5)
                elif oncall_team == 'aws-ams-ops-mgr-on-call':
                    primary = response.json()[3]['oncallMember'][0]
                    time.sleep(0.5)
                schedule_next_day += ONCALL_TEAM_DICT[oncall_team] + "@" + str(primary) + "\n"
            except JSONDecodeError:
                print("On-call name passed does not exist")
        if prev_primary != '':
            print("\nPrimaries who have day off:- \n" + str(prev_primary) + "\nChoosing new Engineers!!\n")
            ##logging.INFO("Primaries who have day off:- \n" + str(prev_primary) + "\nChoosing new Engineers!!\n")
        # generate_dict(nx_dt,date_primaries)        
        # sub_dict[nx_dt]=date_primaries
        dp = f'{nx_dt} : {date_primaries})'
        # print(f'\n{sub_dict}\n')        
        # print(f'\n{date_primaries}\n')
        # r=requests.post(url=OPS_DICT, json={"Content": str(sub_dict)})
        # r=requests.post(url=OPS_DICT, json={"Content": str(date_primaries)})
        r=requests.post(url=OPS_DICT, json={"Content": str(dp)})
        # print(r)
        print(schedule_next_day.strip())
        ##logging.INFO(schedule_next_day.strip())
        print("\nAD Admins: " + str(ad_str))
        ##logging.INFO("AD Admins: " + str(ad_str))

        # Rotate daily primaries in list.txt
        # file_location = Next_DAY_LOG_FILE
        f = open(LISTFILE, 'r+')
        lst = []
        roster = f.read().split(',')
        for i in roster:
            lst.append(i.strip('[ ]').strip('\''))
        for engineer in daily_primaries[::-1]:                  
            try:
                idx = lst.index(engineer)
                lst.pop(idx)
                lst.append(engineer)
            except ValueError:
                print(engineer + " must not be part of on call. Please remove the engineer from on call"
                                " calendar!")
        # Updating list.txt and uploading it in S3 Bucket
        f.truncate(0)
        f.seek(0)
        f.write(str(lst))
        print(f'\n Next Day list file : {lst}')
        ##logging.INFO(lst)
        # fakelist =  ['snekalam', 'ypariyar', 'lusgokha', 'babvis', 'aabhatia', 'umirmuh', 'sulevraj', 'sribat', 'navmadha', 'tpotluri', 'ssraghup', 'nahushkk', 'omidhdp', 'jongovan', 'ambicpal', 'santsink', 'rjonagam', 'saiatt', 'alvijuli']      
        # S3_CLIENT.put_object(Body=str(fakelist), Bucket=S3_BUCKET, Key='list.txt', ACL='bucket-owner-full-control')
        # S3_CLIENT.put_object(Body=str(lst), Bucket=S3_BUCKET, Key='list.txt', ACL='bucket-owner-full-control')
        f.close()
        # info = str(next_date)+" : " + lst
        # r = requests.post(url=IAD_Log_Roster, json={"Content": str(lst)}) 
        r = requests.post(url=IAD_Log_Roster, json={"Content": str(lst)})
        # print(r)
        
        if prev_primary != '':
            # print(message)
            message = "###################################################################################\n" \
                    + "IAD schedule for " + str(next_date) + day_of_week + " Take 1 - \n\n" \
                    + schedule_next_day.strip() + "\nAD Admins: " + str(ad_str).strip() + "\n" \
                    + "\n\n###################################################################################" 
            f = open(URL_LOCAL_FILE, 'r')
            requests.post(url=IAD_Roster, json={"Content": message})
            f.close()
        else:
            # print(message)
            message = "###################################################################################\n" \
                    + "\n**IAD schedule for " + str(next_date) + day_of_week + " Take 1 - \n\n" + schedule_next_day.strip() \
                    + "\nAD Admins: " + str(ad_str).strip()+ "\n\n" \
                    + "\n###################################################################################"
            requests.post(url=IAD_Roster, json={"Content": message})
    # print(sub_dict)
    return None

# ================================================================

def get_primaries_list(day_number):
    """
    This method will get Ops, RFC, SR and Alerts primary in that order from on call calendar
    """
    next_date = datetime.date.today() + datetime.timedelta(days=day_number)
    oncall_list = []
    for oncall_team in TEAM_ALIAS[:6]:
        url = "<redacted>" + str(next_date)
        response = requests.get(url, headers=ONCALL_HEADERS, auth=AUTH)
        # print(response)
        time.sleep(0.5)
        try:
            if oncall_team == 'aws-ams-ops-oncall' or oncall_team == 'aws-ams-ops-eps' or \
                    oncall_team == 'aws-ams-sr-primary' or oncall_team == 'aws-ams-patch-oncall':
                time.sleep(0.3)
                # shifts = response.json()[3]['oncallMember'][0] - Hardcoded values can be used
                # for testing
                shifts = get_primary_from_oncall(next_date, oncall_team)
                oncall_list.append(shifts)
            elif oncall_team == 'aws-ams-alerts-oncall':
                time.sleep(0.3)
                # shifts = response.json()[2]['oncallMember'][0]
                shifts = get_primary_from_oncall(next_date, oncall_team)
                oncall_list.append(shifts)
            elif oncall_team == 'aws-ams-ops-dxc-oncall':
                time.sleep(0.3)
                shifts = response.json()[1]['oncallMember'][0]
                oncall_list.append(shifts)
            elif oncall_team == 'aws-ams-patch-oncall':
                time.sleep(0.3)
                # shifts = response.json()[3]['oncallMember'][0]
                shifts = get_primary_from_oncall(next_date, oncall_team)
                oncall_list.append(shifts)
        except JSONDecodeError:
            print("On-call name passed does not exist")
    return oncall_list

# new - get engineer and if he working in IAD or not. 
def get_primary_from_oncall(next_date, oncall_team):
    # 'aws-ams-ops-oncall', 'aws-ams-rfc-primary', 'aws-ams-sr-primary', 'aws-ams-alerts-oncall'
    # aws-ams-patch-oncall, aws-ams-ops-eps
    url = "<redacted>" + str(next_date)
    
    # print("url is", url)
    response = requests.get(url, headers=ONCALL_HEADERS, auth=AUTH)
    """
    NOTE - Please add engineers accordingly as they get onboarded in the below on_call list
    """
    on_call = ['sribat', 'snekalam', 'babvis', 'aabhatia', 'nairamri', 'lusgokha', 'mmicheda', 'sulevraj', 'hbbandi', 'alekhyal', 'pavanvem', 'chaitrap', 'khanzann']
    # dfw_memebrs list is fetched from constants file. Keep adding new dfw members to the list. 

    on_call = on_call + dfw_memebrs
    len_on_call_members = len(response.json()[0])
    for num in range(len_on_call_members):
        try:
            engineer = response.json()[num]['oncallMember'][0]
            if engineer in on_call:
                # print(engineer)
                return engineer
        except IndexError:
            continue


# testing
def upload_to_on_call(engineer, primary_team_name, rotation_id, day_start):
    """
    Upload changes to On Call
    """
    next_date = datetime.date.today() + datetime.timedelta(days=day_start)
    print(f'{engineer} {primary_team_name} {next_date}')

    #comment below section for testing custom_upload()

    url = "<redacted>" + \
          rotation_id + "/overrides"
    response = requests.get(url, headers=ONCALL_HEADERS, auth=AUTH)

    #Daylight saving is covered. Please make a note of it though when DS begins in November 2021
    start_time = get_shift_start_end_times()[0]
    end_time = get_shift_start_end_times()[1]
    data_params = {
        "members": [engineer],
        "rotationId": rotation_id,
        "start": next_date.strftime("%Y-%m-%dT" + start_time + "Z"),
        "end": next_date.strftime("%Y-%m-%dT" + end_time + "Z"),
        "overrideGap": False
    }
   
    response.raise_for_status()
    data = json.dumps(data_params)
    try:
        response = requests.post(url, headers=ONCALL_HEADERS, auth=AUTH, data=data)
        response.raise_for_status()
        print("hello")
        return True
    except requests.exceptions.HTTPError as err:
        print("error is: ",err)
        return False


def get_shift_start_end_times():
    """
    Get shift start and end times
    Current timings - 10:30 AM (14:30 UTC) to 3:00 PM (19:00 UTC) - this will change automatically,
    after Daylight Saving Time ends, however please make a check before posting schedule

    Use below hardcoded values for testing in future -
    shift_start_time = response.json()[2]['shiftDayOfWeekFilter'][0]['shiftStartTime']
    shift_end_time = response.json()[2]['shiftDayOfWeekFilter'][0]['shiftEndTime']
    """
    response = requests.get(URL_ONCALL, headers=ONCALL_HEADERS, auth=AUTH)
    rotation_weekdays = response.json()
    # print(rotation_weekdays)
    for rotation in rotation_weekdays:
        if 'IAD' in rotation['rotationName']:
            shift_start_time = rotation['shiftDayOfWeekFilter'][0]['shiftStartTime']
    for rotation in rotation_weekdays:
        if 'IAD' in rotation['rotationName']:
            shift_end_time = rotation['shiftDayOfWeekFilter'][0]['shiftEndTime']
    return shift_start_time, shift_end_time

'''
def get_primaries_list(day_number):
    """
    This method will get Ops, RFC, SR and Alerts primary in that order from on call calendar
    """
    next_date = datetime.date.today() + datetime.timedelta(days=day_number)
    oncall_list = []
    for oncall_team in TEAM_ALIAS[:6]:
        url = "<redacted" + str(next_date)
        response = requests.get(url, headers=ONCALL_HEADERS, auth=AUTH)
        print(response)
        time.sleep(0.5)
        try:
            if oncall_team == 'aws-ams-ops-oncall' or oncall_team == 'aws-ams-rfc-primary' or \
                oncall_team == 'aws-ams-sr-primary':
                time.sleep(0.3)
                # shifts = response.json()[3]['oncallMember'][0] - Hardcoded values can be used
                # for testing
                shifts = get_primary_from_oncall(next_date, oncall_team)
                oncall_list.append(shifts)
            elif oncall_team == 'aws-ams-alerts-oncall':
                time.sleep(0.3)
                # shifts = response.json()[2]['oncallMember'][0]
                shifts = get_primary_from_oncall(next_date, oncall_team)
                oncall_list.append(shifts)
            elif oncall_team == 'aws-ams-ops-dxc-oncall':
                time.sleep(0.3)
                shifts = response.json()[1]['oncallMember'][0]
                oncall_list.append(shifts)
            elif oncall_team == 'aws-ams-patch-oncall':
                time.sleep(0.3)
                # shifts = response.json()[3]['oncallMember'][0]
                shifts = get_primary_from_oncall(next_date, oncall_team)
                oncall_list.append(shifts)
        except JSONDecodeError:
            print("On-call name passed does not exist")
    return oncall_list
'''

def find_new_primary(primary, on_call_list, index_num, value, on_call):
    """
    This method will find new primary if an engineer in our on call calendar is some primary AND
    has a day off
    """
    next_date = datetime.date.today() + datetime.timedelta(days=value)

    # on_call = get_engineer_spreadsheet(str(next_date))
    todays_roster = on_call
    index = index_num
    # file_location = LISTFILE
    f = open(LISTFILE, 'r+')
    lst = []
    roster = f.read().split(',')
    ##logging.INFO(roster)
    # The loop below will format the roster in proper "LIST" format and will store it in lst
    for i in roster:
        lst.append(i.strip('[ ]').strip('\''))
    roster_size = len(roster)

    # Find a new primary only when the current primary has day off
    if primary not in on_call or primary in on_call_list :
        # Saving previous primary for future use in else block below
        prev_primary = primary
        for j in range(0, roster_size):
            chosen_one = lst[j]
            if chosen_one in todays_roster and chosen_one not in EXCEPTION:
                primary = chosen_one
                if check_duplicates(chosen_one, on_call_list, index - 1):
                    print("Pick someone else!!")
                else:
                    # Update the on_call_list (List of Ops, RFC, SR and Alerts Primaries)
                    idx_prev_primary = on_call_list.index(prev_primary)
                    on_call_list.pop(idx_prev_primary)
                    on_call_list.append(chosen_one)
                    # Put the selected engineer in the bottom (last element) of the ordered list
                    lst.pop(j)
                    lst.append(chosen_one)
                    # Clear the file contents and then write the new ordered roster list
                    f.truncate(0)
                    f.seek(0)
                    f.write(str(lst))
                    # Upload the roster list on to S3 bucket - This newly uploaded roster list will
                    # be used in next iterations
                    # fakelist =  ['snekalam', 'ypariyar', 'lusgokha', 'babvis', 'aabhatia', 'umirmuh', 'sulevraj', 'sribat', 'navmadha', 'tpotluri', 'ssraghup', 'nahushkk', 'omidhdp', 'jongovan', 'ambicpal', 'santsink', 'rjonagam', 'saiatt', 'alvijuli']      
                    # S3_CLIENT.put_object(Body=str(fakelist), Bucket=S3_BUCKET, Key='list.txt', ACL='bucket-owner-full-control')
                    # S3_CLIENT.put_object(Body=str(lst), Bucket=S3_BUCKET, Key='list.txt', ACL='bucket-owner-full-control')
                    
                    f.close()
                    print("\nNew primary ordered list is - " + str(lst))
                    
                    # f = open(NEXT_DAY_LOCAL_FILE_URL, 'r')
                    requests.post(url=IAD_Roster, json={"Content": lst})                    
                    ##logging.INFO("\nNew primary ordered list is - " + str(lst))
                    break
    return [primary, on_call_list]

def find_new_eps_primary(primary, on_call_list, index_num, value, on_call):
    """
    This method will find new primary if an engineer in our on call calendar is some primary AND
    has a day off
    """
    next_date = datetime.date.today() + datetime.timedelta(days=value)

    # on_call = get_engineer_spreadsheet(str(next_date))
    todays_roster = on_call
    index = index_num
    # file_location = LISTFILE
    f = open(LISTFILE, 'r+')
    lst = []
    roster = f.read().split(',')
    ##logging.INFO(roster)
    # The loop below will format the roster in proper "LIST" format and will store it in lst
    for i in roster:
        lst.append(i.strip('[ ]').strip('\''))
    roster_size = len(roster)

    # Find a new primary only when the current primary has day off
    if primary not in on_call or primary in on_call_list :
        # Saving previous primary for future use in else block below
        prev_primary = primary
        for j in range(0, roster_size):
            chosen_one = lst[j]
            if chosen_one in todays_roster and chosen_one in EPSLIST:
                primary = chosen_one
                if check_duplicates(chosen_one, on_call_list, index - 1):
                    print("Pick someone else!!")
                else:
                    # Update the on_call_list (List of Ops, RFC, SR and Alerts Primaries)
                    idx_prev_primary = on_call_list.index(prev_primary)
                    on_call_list.pop(idx_prev_primary)
                    on_call_list.append(chosen_one)
                    # Put the selected engineer in the bottom (last element) of the ordered list
                    lst.pop(j)
                    lst.append(chosen_one)
                    # Clear the file contents and then write the new ordered roster list
                    f.truncate(0)
                    f.seek(0)
                    f.write(str(lst))
                    # Upload the roster list on to S3 bucket - This newly uploaded roster list will
                    # be used in next iterations
                    # fakelist =  ['snekalam', 'ypariyar', 'lusgokha', 'babvis', 'aabhatia', 'umirmuh', 'sulevraj', 'sribat', 'navmadha', 'tpotluri', 'ssraghup', 'nahushkk', 'omidhdp', 'jongovan', 'ambicpal', 'santsink', 'nairamri', 'pavanvem', 'alvijuli']      
                    # S3_CLIENT.put_object(Body=str(fakelist), Bucket=S3_BUCKET, Key='list.txt', ACL='bucket-owner-full-control')
                    # S3_CLIENT.put_object(Body=str(lst), Bucket=S3_BUCKET, Key='list.txt', ACL='bucket-owner-full-control')
                    
                    f.close()
                    print("\nNew primary ordered list is - " + str(lst))
                    
                    # f = open(NEXT_DAY_LOCAL_FILE_URL, 'r')
                    requests.post(url=IAD_Roster, json={"Content": lst})                    
                    ##logging.INFO("\nNew primary ordered list is - " + str(lst))
                    break
    return [primary, on_call_list]

def find_new_patch_primary(primary, on_call_list, index_num, value, on_call):
    """
    This method will find new primary if an engineer in our on call calendar is some primary AND
    has a day off
    """
    next_date = datetime.date.today() + datetime.timedelta(days=value)

    # on_call = get_engineer_spreadsheet(str(next_date))
    todays_roster = on_call
    index = index_num
    # file_location = LISTFILE
    f = open(LISTFILE, 'r+')
    lst = []
    roster = f.read().split(',')
    ##logging.INFO(roster)
    # The loop below will format the roster in proper "LIST" format and will store it in lst
    for i in roster:
        lst.append(i.strip('[ ]').strip('\''))
    roster_size = len(roster)

    # Find a new primary only when the current primary has day off
    if primary not in on_call or primary in on_call_list :
        # Saving previous primary for future use in else block below
        prev_primary = primary
        for j in range(0, roster_size):
            chosen_one = lst[j]
            if chosen_one in todays_roster and chosen_one in PATCHLIST:
                primary = chosen_one
                if check_duplicates(chosen_one, on_call_list, index - 1):
                    print("Pick someone else!!")
                else:
                    # Update the on_call_list (List of Ops, RFC, SR and Alerts Primaries)
                    idx_prev_primary = on_call_list.index(prev_primary)
                    on_call_list.pop(idx_prev_primary)
                    on_call_list.append(chosen_one)
                    # Put the selected engineer in the bottom (last element) of the ordered list
                    lst.pop(j)
                    lst.append(chosen_one)
                    # Clear the file contents and then write the new ordered roster list
                    f.truncate(0)
                    f.seek(0)
                    f.write(str(lst))
                    # Upload the roster list on to S3 bucket - This newly uploaded roster list will
                    # be used in next iterations
                    # fakelist =  ['snekalam', 'ypariyar', 'lusgokha', 'babvis', 'aabhatia', 'umirmuh', 'sulevraj', 'sribat', 'navmadha', 'tpotluri', 'ssraghup', 'nahushkk', 'omidhdp', 'jongovan', 'ambicpal', 'santsink', 'nairamri', 'pavanvem', 'alvijuli']      
                    # S3_CLIENT.put_object(Body=str(fakelist), Bucket=S3_BUCKET, Key='list.txt', ACL='bucket-owner-full-control')
                    # S3_CLIENT.put_object(Body=str(lst), Bucket=S3_BUCKET, Key='list.txt', ACL='bucket-owner-full-control')
                    
                    f.close()
                    print("\nNew primary ordered list is - " + str(lst))
                    
                    # f = open(NEXT_DAY_LOCAL_FILE_URL, 'r')
                    requests.post(url=IAD_Roster, json={"Content": lst})                    
                    ##logging.INFO("\nNew primary ordered list is - " + str(lst))
                    break
    return [primary, on_call_list]


def check_duplicates(tech_name, on_call_list, index_num):
    """
    Method checks for duplicity for a picked primary from the roster
    """
    on_call = on_call_list
    duplicate_check_list = on_call
    for i in range(0, index_num):
        duplicate_check_list.pop(i)
    if tech_name in duplicate_check_list:
        print("You have a duplicate primary @" + tech_name)
        return True
    return False

def get_engineer_spreadsheet(*month_date):
    """
    This method is used to find engineers available to work in a given day
    USAGE -
    get_engineer_spreadsheet('2021-06-06') will return engineer aliases available on June 6, 2021
    """

    engineer_count = 87
    # Row number of engineer's alias in Excel sheet
    # New spreadsheet row value for engineer alias is 0
    engineer_alias_xls = 0
    for dt in month_date:   
        on_call_engineers = []
        on_call_dfw_engineers =[]
        value = MAP_DATE_XLS[dt]
        # print(dt, value, engineer_count)
        for engineer_names in range(0, engineer_count):
            # Get value of date's cell value from spreadsheet
            # Get time slot rows
            # Use this to determine who is available for a given day's schedule
            # print(f'SheetRowValues {SHEET.row_values(value)}')
            # print(SHEET.row_values)
            time_slots = SHEET.row_values(value)[1:88]
            # print(f'SheetRowValues {time_slots}')
            # Check if time slot cell value is not empty & not night shift (11:00 PM to 7:00 AM)
            if time_slots[engineer_names] != '' and time_slots[engineer_names] != 'US SOIL' and \
                    time_slots[engineer_names] != 'PROJECT' and time_slots[engineer_names] != 'PTO' and \
                    time_slots[engineer_names] != 'COMP DAY'and time_slots[engineer_names] != 'NHT' and \
                    time_slots[engineer_names] != 'NIGHTS' and time_slots[engineer_names] != 'LOA' and \
                    time_slots[engineer_names] != 'Training + 12-5':
                # Get 7:00 AM to 3:00 PM and 9:00 AM to 5:00 PM cell values
                if time_slots[engineer_names] == '09:00-17:00' or time_slots[engineer_names] \
                        == '10:30-3:30 + Training':
                    on_call_engineers.append(
                        SHEET.cell_value(engineer_alias_xls, engineer_names + 1))
                elif time_slots[engineer_names] == '07:00-15:00':
                    on_call_engineers.append(
                        SHEET.cell_value(engineer_alias_xls, engineer_names + 1)
                        + " - 7:00 AM to 3:00 PM")  
                elif time_slots[engineer_names] == '10:00-18:00' or time_slots[engineer_names] \
                        == '10:00-15:00 + Training':
                    on_call_dfw_engineers.append(
                        SHEET.cell_value(engineer_alias_xls, engineer_names + 1))          

        print("\n#########################################################")
        print("\nAvailable IAD engineers for " + dt + " - " + str(on_call_engineers))
        print("\nAvailable DFW engineers for " + dt + " - " + str(on_call_dfw_engineers))


    return on_call_engineers + on_call_dfw_engineers

def get_security(next_date):
    """
    This method will find security on call
    """
    url = "<redacted>" + str(next_date)
    response = requests.get(url, headers=ONCALL_HEADERS, auth=AUTH)
    security_list = ['brybi','sherco','brandon','ryjohnn']
    dub_list = ['vttachev', 'plip'] # might need this from November to March during Daylight savings
    
    len_security_on_call = len(response.json()[0])
    sec_on_call = ""
    for i in range(len_security_on_call):
        try:
            sec_guy = response.json()[i]['oncallMember'][0]
            if sec_guy in security_list:
                sec_on_call += sec_guy
        except IndexError:
            continue
    return sec_on_call

def test_get_rot_id():
    # ONLY FOR TESTING
    # Using this method only to get rotation IDs from On Call
    # Cmd + F for IAD from output and look for rotationId
    url = "<redacted>"
    # print(url)
    response = requests.get(url, headers=ONCALL_HEADERS, auth=AUTH, verify=False)
    response.raise_for_status()
    print(response.json())

def add_primaries_to_dict(primary,day_start):
    keys=["OpsPrimary","SrPrimary","IncPrimary"]
    date_primaries = {}    

    for variable in keys:
        date_primaries[variable] = primary

def generate_dict(nx_dt,date_pri):    
    SUB_DICT[nx_dt]=date_pri

# =========================================================================================

#uncomment the upload code from the above upload function

#sdate = date value like "2022-04-16" will be 16
#upload_to_on_call will except the value nextdate + sdate. So based on the date of execution pass the number to minus from key value 

def custom_upload():
    for key,value in pri.items():    
        #Before running comment the upload section and check the date
        #Iter1 LastRun details ExectionDate :04-28-2022, List from '05-01-2022' # Diffvalue = 2
        #Iter1 LastRun details ExectionDate :05-15-2022, List from '05-016-2022' # Diffvalue = -15
        
        Diffvalue = -15
        # the day I want to start from + diffvalue = day_start
        sdate=int(key.split('-')[1]) + Diffvalue
        # print(value['Ops Primary: '],int(sdate))
        upload_to_on_call(value['Ops Primary: '], 'aws-ams-ops-oncall', OPS_PRIM_ROT_ID, int(sdate))
        upload_to_on_call(value['Queue Primary: '], 'aws-ams-sr-primary', SR_ROT_ID, sdate)
        upload_to_on_call(value['EPS On Call: '], 'aws-ams-ops-eps', EPS_ROT_ID, sdate)
        upload_to_on_call(value['Patch Primary: '], 'aws-ams-patch-oncall', PATCH_ROT_ID, sdate)
        # upload_to_on_call(value['Alerts/Incidents Primary: '], 'aws-ams-alerts-oncall', ALERTS_ROT_ID, sdate)
        # time.sleep(2)
        print("\n")


