# global variables for this script

# timezone of all data
from pytz import timezone
tz = timezone('America/Toronto')

# where the data from OTP is
input_dir = '/home/nate/dissdata/routing/'

# define time window to clip to
import datetime as dt 
start = dt.time(6,30,0) # h,m,s; 6:30am
end = dt.time(22,0,0) # h,m,s;  10:00pm

# (http://dev.opentripplanner.org/apidoc/1.0.0/resource_PlannerResource.html)
walk_speed = 1.34112 # 3mph in meters per second 
