# global variables for this script

# timezone of all data
from pytz import timezone
tz = timezone('America/Toronto')

# where the data from OTP is
input_dir = '/home/nate/dissdata/routing/'

# define time window to clip travel to
import datetime as dt
window_start_time = dt.time(19,0,0) # h,m,s 
window_end_time   = dt.time(22,0,0) # h,m,s
# dates limits are inclusive
window_start_date = dt.date(2017,11,6)
window_end_date = dt.date(2017,11,10)

# (http://dev.opentripplanner.org/apidoc/1.0.0/resource_PlannerResource.html)
walk_speed = 1.34112 # 3mph in meters per second 

# DB connection details
DB_conn = "host='localhost' dbname='routing' user='nate' password='mink'" 
