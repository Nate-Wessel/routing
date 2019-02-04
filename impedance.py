# ACCESS AND IMPEDANCE FUNCTIONS
import math, config, db
from misc import *
import datetime as dt

def cum(td,theta=45):
	"""Cumulative accessibility function. Accepts a timedelta and returns a 
	binary measure. Theta is in minutes."""
	return 0 if td.total_seconds()/60. < theta else 1

def negexp(td,beta=30):
	"""Negative exponential distance decay function with parameter in minutes."""
	return math.exp( -( td.total_seconds() / 60. / beta ) )

def habitual_times(OD):
	"""Return a set of travel times over the time window for the assumption that
	travellers consistently take the itinerary which minimizes mean travel
	time."""
	habit_itin = None
	current_best_times = [dt.timedelta(seconds=99999999999)]
	# look up times on all viable itineraries, keeping the best times
	for itin in OD.alter_itins('retro'):
		if itin.is_walking:
			walk_time = dt.timedelta(seconds=itin.walk_distance/config.walk_speed)
			if seconds_walking <= mtd(current_best_times):
				current_best_times = [ seconds_walking ]
				habit_itin = itin
		else:
			# this trip involves transit and we need to look up trips in the DB
			trips = db.all_itinerary_trips(itin)
			clip_trips_to_window(trips)
			times = trips2times(trips)
			if mtd(times) <= mtd(current_best_times):
				current_best_times = times
				habit_itin = itin
	if habit_itin:
		print(habit_itin)
		return current_best_times

def mtd(td_list):
	"""Mean TimeDelta"""
	# convert to seconds, take the mean, return a timedelta
	sec_list = [ td.total_seconds() for td in td_list ]
	return dt.timedelta( seconds=(sum(sec_list)/len(td_list)) )
