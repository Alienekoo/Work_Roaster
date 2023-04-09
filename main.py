from customfns import get_next_day_assignments, upload_to_on_call, custom_upload
from constants import *
from  prilistdate import pri
import sys
import time

def main():
    get_next_day_assignments()
    # generate_map_xls()
    # validate_oncall()
    # test_next_day_assignments(True)
    # test_get_rot_id()
    
    # custom_upload()
    #date parameter will accept 1 is next_date    
    # get_primaries_list


if __name__ == "__main__":
    main()