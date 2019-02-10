import re
from datetime import datetime
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


class Itinerary(Path):
	"""Characterizes a typical strategy common to trips on an OD."""
	
	def __init__(self,path_instance):
		"""constructed from an arbitrary path instance"""
		Path.__init__(self,path_instance.otp_string)
		self.OTP_trips = []
		self.DB_trips = None
		self.prob = 0

	def __hash__(self):
		"""This is to override the Path method only. this function is not to be 
		used."""
		assert False # we should not be here. 

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
		# add the trip if valid
		if trip_to_add.path != self or trip_to_add in self.OTP_trips: return 
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

