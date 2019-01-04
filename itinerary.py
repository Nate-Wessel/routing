# miscelaneous functions 

class Itinerary(object):
	"""represents a distinct way of getting from A to B - a route strategy."""

	def __init__(self,itinerary):
		"""Parse an itinerary from get-itineraries.py. 
		e.g. '{w28,s2773,r45,s2859,w42,s3280,r300,s7168,w36}' """
		self.walk_speed = 2 # meters / second
		self.original_itinerary = itinerary
		self.segments = [] # segment starts with walking to a stop, ends at a stop
		# remove SQL brackets
		itinerary = itinerary.strip('{}')
		steps = itinerary.split(',')
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

	@property
	def o_stops(self):
		"""return an ordered list of origin stops"""
		return [ s['stop1'] for s in self.segments ]
	@property
	def d_stops(self):
		"""return an ordered list of origin stops"""
		return [ s['stop2'] for s in self.segments ]
	@property
	def routes(self):
		"""return an ordered list of origin stops"""
		return [ s['route'] for s in self.segments ]
	@property
	def walk_distance(self):
		"""return an ordered list of origin stops"""
		return sum( [ s['walk'] for s in self.segments ] ) + self.final_walk
