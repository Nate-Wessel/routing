import re
from datetime import datetime, timedelta
import db, config

class Path:
	"""Represents the path of a particular trip."""

	def __init__(self,otp_string):
		"""Parse a path from get-itineraries.py,
		e.g. '{w28,s2773,r45,s2859,w42,s3280,r300,s7168,w36}'."""
		self.otp_string = otp_string.replace('_','')

	def __repr__(self):
		"""Just the original path string used to construct the object"""
		return self.otp_string

	def __eq__(self,other):
		"""Equality is approximate to account for only-slightly-different paths."""
		return self.letters == other.letters and (
			self.routes == other.routes or self.stops == other.stops
		)
	def __hash__(self):
		"""This is based only on the OTP String."""
		return hash(self.otp_string)

	@property
	def letters(self):
		"""Step type sequence of the path. 
		e.g. from '{w838,s9600,r506,s9614,w583}' to 'wsrsw' """
		return ''.join( re.findall(r'[wsr]',self.otp_string) )
	@property
	def routes(self):
		"""Route names in sequence as a string. Used for comparison."""
		return re.findall('(?<=r)\d+',self.otp_string)
	@property
	def stops(self):
		"""Stop IDs in sequence as a string. Used for comarison."""
		return ';'.join( re.findall('(?<=s)\d+',self.otp_string) )

	@property
	def first_walk_duration(self):
		"""How long should the first walking segment take - returns a timedelta."""
		meters = int(re.search('(?<=w)\d+',self.otp_string).group())
		return timedelta( seconds=( meters / config.walk_speed ) )


class Itinerary(Path):
	"""Characterizes a typical strategy common to trips on an OD."""
	
	def __init__(self,path_instance):
		"""constructed from an arbitrary path instance"""
		Path.__init__(self,path_instance.otp_string)
		self.OTP_trips = []
		self.DB_trips = None
		self.DB_departures = None
		self.DB_mean_travel_time = None
		self.prob = 0

#	def __hash__(self):
#		"""This is to override the Path method only. this function is not to be 
#		used."""
#		assert False # we should not be here. 

	@property
	def mean_travel_time(self):
		"""Mean travel time on DB trips inside the sampling window."""
		# pull it out of memory if we have it already
		if not self.DB_mean_travel_time:
			if self.is_walking:
				self.DB_mean_travel_time = self.walk_time
			else:
				departures = [ d for d in self.departures if d.travel_time ]
				seconds = [ d.travel_time.total_seconds() for d in departures ]
				mean_seconds = sum(seconds) / len(seconds)
				self.DB_mean_travel_time = timedelta(seconds=mean_seconds)
		return self.DB_mean_travel_time

	@property
	def departures(self):
		"""Departures in the time window using only this itinerary."""
		# pull it out of memory if we've already got this
		if not self.DB_departures:
			from triptools import sample_times
			from departure import Departure
			##############
			if self.is_walking: # all departures are the same
				self.DB_departures = [ 
					Departure(time,None,self) for time in sample_times() 
				]
			else: # trip based departures
				# get trips sorted (first to last) by departure
				trips = sorted( self.get_trips(), key=lambda t: t.depart_ts )
				self.DB_departures, i = [], 0
				for time in sample_times():
					# move the trip index up to the present time if necessary
					while i < len(trips) and trips[i].depart < time: 
						i += 1
					if i < len(trips): # we still have trips
						self.DB_departures.append( Departure(time,trips[i]) )
					else: # we've run out of trips
						self.DB_departures.append( Departure(time,None) )
		return self.DB_departures
		

	def get_trips(self):
		"""Get all trips corresponding to this itinerary (from the database)."""
		if not self.DB_trips:
			if not self.is_walking:
				self.DB_trips = db.all_itinerary_trips(self)
			else:
				# create a single walking trip at the start of the time window
				from trip import Trip
				walk_seconds = self.total_walk_distance / config.walk_speed
				unix_trip_start = config.tz.localize( datetime.combine(
					config.window_start_date,config.window_start_time
				)).timestamp()
				self.DB_trips = [Trip(
					unix_trip_start,
					unix_trip_start + walk_seconds,
					self.otp_string
				)]
		return self.DB_trips

	def add_OTP_trip(self,trip_to_add):
		"""Add a trip which uses this itinerary. Update to the most common path 
		if necessary."""
		# ensure the trip is valid
		assert trip_to_add.path == self
		assert trip_to_add not in self.OTP_trips
		self.OTP_trips.append(trip_to_add)
		# check that we still have the most common itinerary
		if trip_to_add.path.otp_string != self.otp_string:
			# count up the frequencies of each of the contenders
			tug_o_war = 0
			for trip in self.OTP_trips:
				if trip.path.otp_string == self.otp_string:
					tug_o_war += 1
				elif trip.path.otp_string == trip_to_add.path.otp_string:
					tug_o_war -= 1
			# Did the contender beat the current champion?
			if tug_o_war < 0: 
				self.otp_string = trip_to_add.path.otp_string

	@property
	def total_time(self):
		"""Total time of optimality of all trips"""
		return sum([trip.time_before for trip in self.OTP_trips])

	@property
	def is_walking(self):
		"""Is this just walking with no transit?"""
		return len(self.routes) == 0

	@property
	def o_stops(self):
		"""Return an ordered list of origin stops"""
		matches = re.findall('(?<=s)\d+(?=,r)',self.otp_string)
		return [int(s) for s in matches]

	@property
	def d_stops(self):
		"""Return an ordered list of destination stops"""
		# this is done in two steps as variable length lookbehinds are not allowed
		routes_and_stops = re.findall('r\d+,s\d+',self.otp_string)
		return [ int(re.search('(?<=s)\d+',m).group()) for m in routes_and_stops ]

	@property
	def total_walk_distance(self):
		"""Return the total walking distance in meters"""
		walks = re.findall('(?<=w)\d+',self.otp_string)
		return sum([int(walk) for walk in walks])

	@property
	def walk_time(self):
		"""End to end walk time, None if this is not a walking-only itinerary."""
		if not self.is_walking: return None
		return timedelta(seconds=self.total_walk_distance/config.walk_speed)

	@property
	def walk_times(self):
		"""Return time (seconds) required for each walk leg. This is used directly 
		only in the db module."""
		walk_times = []
		# check for explicit walk segments OR stops with no intermediate walk
		matches = re.findall('w\d+|r\d+,[s\d+,]+(?=r)',self.otp_string)
		for m in matches:
			if m[0] == 'w': walk_times.append( int(m[1:]) / config.walk_speed )
			else: walk_times.append( 5 ) # +5s for no-walking transfer
		return walk_times

