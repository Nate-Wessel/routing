from datetime import datetime as dt
import db, config
from itinerary import Path
import pytz

class Trip:
	"""One (shortest?) trip"""
	def __init__(self,depart,arrive,path_string):
		# unix timestamps
		self.depart_ts = float(depart)
		self.arrive_ts = float(arrive)
		# localized datetime's
		self.depart = pytz.utc.localize( 
			dt.utcfromtimestamp(self.depart_ts) 
		).astimezone(config.tz)
		self.arrive = pytz.utc.localize( 
			dt.utcfromtimestamp(self.arrive_ts) 
		).astimezone(config.tz)
		# path can either be a path object or a string (from OTP script)
		self.path = Path(path_string)
		self.time_before = 0 # time from previous fastest trip

	def __repr__(self):
		return '\tTrip=depart:{},arrive:{},via:{}'.format(
			self.depart.time(), self.arrive.time(), self.path )

	@property
	def duration(self):
		"""duration of trip as timedelta"""
		return self.arrive - self.depart

	@property
	def first_boarding_time(self):
		"""time that the first vehicle would be boarded if any"""
		return self.depart + self.path.first_walk_duration
		

# TODO just roping this off for a moment instead of refactoring it now
#	def verify(self):
#		"""Try to verify that this trip, or something close to it, exists in the 
#		database."""
#		# iterate over *route* segments
#		time = self.depart_ts
#		for i, step in enumerate( self.path.segments ):
#			expected_route = step['route']
#			# Query the database about this supposed trip
#			# pushing time forward from the departure to the arrival at the next stop
#			( time, route_id ) = db.o2d_at( 
#				step['stop1'], 
#				step['stop2'], 
#				time + step['walk']/config.walk_speed
#			)
#			# make sure we got some result
#			if not route_id:
#				print('\t',expected_route,'segment not confirmed')
#				return
#			if route_id != expected_route:
#				print('\tdifferent route used:',route_id,'but expected',expected_route)
#		# add time for walking to the final destination
#		time += self.path.final_walk / config.walk_speed
#		diff_pct = (time-self.arrive_ts) / (self.arrive_ts-self.depart_ts)
#		print('\t{:+.2%}'.format(diff_pct) , self.path )

