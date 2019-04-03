import os, csv
from math import log
from datetime import datetime, timedelta
import config, db, triptools
from trip import Trip
from departure import Departure

class OD:
	"""An O->D pair"""
	def __init__(self,origin,dest):
		"""origin and dest are integer IDs"""
		self.orig = origin
		self.dest = dest
		# read in the trip itineraries
		self.trips = self.get_trips_from_file()
		#triptools.allocate_time(self.trips)
		# summarize itinerary data
		self.itins = triptools.summarize_paths(self.trips)
		# get list of optimal departures
		self.optimal_departures = self.get_optimal_departures()
		# assign probabilities to departures
		self.assign_probs()

	def __repr__(self):
		name = str(self.orig)+' -> '+str(self.dest)
		stats = '\n\tentropy:{} | trips:{}'.format( 
			round(self.entropy,4), len(self.trips) )
		for itin in self.alter_itins():
			stats += '\n\t\tPr:{}, '.format( round(itin.prob,2) )
			stats += 'It:{}'.format( itin ) 
		return( name + stats )

	def assign_probs(self):
		"""Assign P_i values based on participation in optimal departures.
		Drop any itineraries with no optimal departures."""
		optimal_paths = [ dep.path for dep in self.optimal_departures ]
		#get frequency counts
		count = {}
		for path in optimal_paths:
			if path in count: count[path] += 1
			else:             count[path] =  1
		for path in optimal_paths:
			for i, itin in enumerate(self.itins):
				if path == itin: 
					itin.prob = count[path] / len(optimal_paths)
					break
		# drop any p==0 itins
		self.itins = [ it for it in self.itins if it.prob > 0 ]
		# sort by prob
		self.itins.sort(key=lambda i: i.prob, reverse=True)

	def alter_itins(self):
		"""Return a list of itineraries"""
		return self.itins

	def get_trips_from_file(self):
		"""Check files for trips data and read it into a list. Remove any trips
		outside the time window as well as any suboptimal trips."""
		# directories to check 
		directories = ['17476','17477','17478','17479','17480']
		trips = []
		for d in directories:
			csvpath = config.input_dir+d+'/'+str(self.orig)+'/'+str(self.dest)+'.csv'
			if not os.path.exists(csvpath): continue			
			with open(csvpath) as f:
				reader = csv.DictReader(f)	
				trips.extend( 
					[ Trip(r['depart'],r['arrive'],r['itinerary']) for r in reader ]
				)
		# we now have all the data from the files but need to clean it
		triptools.clip_trips_to_window(trips)
		triptools.remove_premature_departures(trips)
		return trips

	def get_optimal_departures(self):
		"""Return a set of sampled travel times which are as fast as possible, and 
		indifferent to route choice. This is the status quo."""
		# get all possible trips and any walking alternatives
		departures, all_trips, walk = [], [], None
		for itin in self.alter_itins():
			if not walk and itin.is_walking: 
				walk = itin
			else: # itin has transit
				all_trips.extend( itin.get_trips() )
		# if we have only walking, then all trips will be walking
		if walk and len(self.alter_itins()) == 1:
			return [ Departure(t,None,walk) for t in triptools.sample_times() ]
		# we now have only trips or trips and a walking option
		triptools.remove_premature_departures(all_trips)
		# ensure trips are sorted by departure, ASC
		optimal_trips = sorted(all_trips, key=lambda x: x.depart_ts)
		# iterate over sample moments looking for arrival of next-departing trip
		i = 0
		for time in triptools.sample_times():
			# move the trip index up to the present time if necessary
			while i < len(optimal_trips) and optimal_trips[i].depart <= time: i += 1
			# no trips left or walking better option
			if ( i >= len(optimal_trips) or (
				walk and (optimal_trips[i].arrive-time) > walk.walk_time
			) ):
				departures.append( Departure( time, None, walk ) )
			# have trip better than walking if that was available
			elif i < len(optimal_trips):
				departures.append( Departure( time, optimal_trips[i] ) )
			# no trip or attractive walking option
			else:
				departures.append( Departure( time ) )
		return departures


	@property
	def habit_departures(self):
		"""Return a set of travel times over the time window for the assumption 
		that travellers consistently take the itinerary which minimizes mean 
		travel time."""
		habit_itin = None
		best_time = None
		# find the best mean travel time
		for itin in self.alter_itins():
			if ( (not best_time) or itin.mean_travel_time < best_time ):
				best_time = itin.mean_travel_time
				habit_itin = itin
		if habit_itin:
			return habit_itin.departures
		else:
			return [ Departure(time) for time in triptools.sample_times() ]
	
	@property
	def realtime_departures(self):
		"""Select an itinerary by trying to minimize the time before first 
		boarding a vehicle. Initial walking and waiting are treated indifferently. 
		From itineraries with identical departure times (due to shared first leg), 
		the one with the better mean travel time is chosen."""
		# get a big list of all possible trips, noting any end to end walking options	
		departures, all_trips, walk = [], [], None
		# for itineraries sorted in order of mean travel time:
		for itin in sorted(self.alter_itins(),key=lambda i: i.mean_travel_time):
			if not walk and itin.is_walking: walk = itin
			# extend right
			else: all_trips.extend( itin.get_trips() )
		# if we have only walking, then all trips will be walking
		if walk and len(self.alter_itins()) == 1:
			return [ Departure(t,None,walk) for t in triptools.sample_times() ]
		# we now have only trips or trips and a walking option
		# this is already sorted by mean itinerary travel time
		# now also (stably) sort by departure minus initial walk
		trips = sorted(all_trips, key=lambda t: t.first_boarding_time)
		# iterate over sample moments looking for arrival of next-departing trip
		i = 0
		for time in triptools.sample_times():
			# move the trip index up to the present time if necessary
			# there will be entries with identical departure times and this will 
			# take the first, which has an itinerary with a better mean travel time 
			while i < len(trips) and trips[i].depart <= time: i += 1
			# we still have trips
			if i < len(trips):
				# if no walking or trip is better
				if (not walk) or trips[i].first_boarding_time < time + walk.walk_time:
					departures.append( Departure( time, trips[i] ) )
				else: # walking is the better option
					departures.append( Departure( time, None, walk ) )
			# no trips left
			else: 
				departures.append( Departure( time, None, walk ) )
		return departures

	@property
	def entropy(self):
		"""Base-2 Shannon Entropy of optimal departures"""
		departures = self.optimal_departures
		optimal_paths = [ dep.path for dep in departures if dep.path ]
		#get frequency counts
		c = {}
		for path in optimal_paths:
			if path in c:
				c[path] += 1
			else:
				c[path] = 1
		# frequency to P values and calculate entropy
		P = [ c[key]/len(optimal_paths) for key in c ]
		return - sum( [ P_i * log(P_i,2) for P_i in P ] )

