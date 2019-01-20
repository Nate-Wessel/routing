# ACCESS FUNCTIONS
import math

def cum(td,theta=45):
	"""Cumulative accessibility function. Accepts a timedelta and returns a 
	binary measure. Theta is in minutes."""
	return 0 if td.total_seconds()/60. < theta else 1

def negexp(td,beta=30):
	"""Negative exponential distance decay function with parameter in minutes."""
	return math.exp( -( td.total_seconds() / 60. / beta ) )
