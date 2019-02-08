import re

class Path:
	"""Represents the path of a particular trip."""

	def __init__(self,otp_string):
		"""Parse a path from get-itineraries.py,
		e.g. '{w28,s2773,r45,s2859,w42,s3280,r300,s7168,w36}'."""
		self.otp_string = otp_string

	def __repr__(self):
		"""Just the original path string used to construct the object"""
		return self.otp_string

	def __eq__(self,other):
		"""Equality is approximate to account for only-slightly-different paths."""
		return self.letters == other.letters and (
			self.routes == other.routes or self.stops == other.stops
		)

	@property
	def letters(self):
		"""Step type sequence of the path. 
		e.g. from '{w838,s9600,r506,s9614,w583}' to 'wsrsw' """
		return ''.join( re.findall(r'[wsr]',self.otp_string) )
	@property
	def routes(self):
		"""Route names in sequence as a string. Used for comparison."""
		return ';'.join( re.findall('(?<=r)\d+',self.otp_string) )
	@property
	def stops(self):
		"""Stop IDs in sequence as a string. Used for comarison."""
		return ';'.join( re.findall('(?<=s)\d+',self.otp_string) )

class Itinerary(Path):
	"""Characterizes a typical strategy common to trips on an OD."""
	
	def __init__(self,path_instance):
		"""constructed from an arbitrary path instance"""
		Path.__init__(self,path_instance.otp_string)
		self.segments = [] # segment starts with walking to a stop, ends at a stop
		# remove SQL brackets and break on commas
		steps = self.otp_string.strip('{}').split(',')
		# assign length of final walk
		self.final_walk = int(steps[-1][1:]) if steps[-1][0] == 'w' else 0
		# iterate over *route* segments, looking forward and back for other data
		for i, step in enumerate( steps ):
			if step[0] != 'r': 
				continue
			# make sure we know where stuff is
			assert steps[i-1][0] == 's' and steps[i+1][0] == 's'
			stop1 = int(steps[i-1][1:].rstrip('_'))
			stop2 = int(steps[i+1][1:].rstrip('_'))
			if steps[i-2][0] == 'w':
				walk = int(steps[i-2][1:])
			route = step[1:]
			# get IDs of stops for boarding and disembarking
			self.segments.append( {
				'walk':walk, 'stop1':stop1, 'stop2':stop2, 'route':route
			} )

		self.trips = []
		self.prob = 0
		
	def add_trip(self,trip):
		self.trips.append(trip)

	@property
	def total_time(self):
		"""Total time of optimality of all trips"""
		return sum([trip.time_before for trip in self.trips])

	@property
	def is_walking(self):
		"""Is this just walking with no transit?"""
		return len(self.segments) == 0

	@property
	def o_stops(self):
		"""Return an ordered list of origin stops"""
		return [ s['stop1'] for s in self.segments ]

	@property
	def d_stops(self):
		"""Return an ordered list of origin stops"""
		return [ s['stop2'] for s in self.segments ]

	@property
	def walk_distance(self):
		"""Return the total walking distance in meters"""
		return sum( [ s['walk'] for s in self.segments ] ) + self.final_walk

#	@property
#	def collapsed_routes(self):
#		"""Same as routes, but collapses any identical subsequent routes."""
#		all_routes = self.routes
#		if len(all_routes) <= 1 or len(all_routes) == len(set(all_routes)):
#			return all_routes
#		else: # else cleaning is necessary
#			cleaned_routes = [all_routes[0]]
#			for i, route in enumerate(all_routes):
#				if i > 0 and route != all_routes[i-1]:
#					cleaned_routes.append(route)
#			return cleaned_routes
