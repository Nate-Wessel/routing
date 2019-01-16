# global variables for this script
from pytz import timezone
import datetime as dt

# timezone of all data
tz = timezone('America/Toronto')

# where the data from OTP is
input_dir = '/home/nate/dissdata/routing/'

# define time window to clip to 
start = dt.time(6,30,0) # h,m,s; 6:30am
end = dt.time(22,0,0) # h,m,s;  10:00pm

walk_speed = 1.34112 # 3mph in meters per second 
# (http://dev.opentripplanner.org/apidoc/1.0.0/resource_PlannerResource.html)
