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
		self.retro_trips = self.get_trips_from_file('retro')
		self.sched_trips = self.get_trips_from_file('sched')
		triptools.allocate_time(self.sched_trips)
		triptools.allocate_time(self.retro_trips)
		# summarize itinerary data
		self.sched_itins = triptools.summarize_paths(self.sched_trips)
		self.retro_itins = triptools.summarize_paths(self.retro_trips)
		# store optimal departures once generated
		self.optimal_departures_list = None

	def __repr__(self):
		name = str(self.orig)+' -> '+str(self.dest)
		sched = '\n\tsched | entropy:{} | trips:{}'.format( 
			round(self.sched_entropy,2), len(self.sched_trips) )
		retro = '\n\tretro | entropy:{} | trips:{}'.format( 
			round(self.retro_entropy,2), len(self.retro_trips) )
		for itin in self.alter_itins():
			retro += '\n\t\tPr:{}, '.format( round(itin.prob,2) )
			retro += 'It:{}'.format( itin ) 
		for itin in self.alter_itins('sched'):
			sched += '\n\t\tPr:{}, '.format( round(itin.prob,2) )
			sched += 'It:{}'.format( itin )
		return( name + sched + retro )

	def alter_itins(self,kind='retro'):
		"""Return a list of itineraries where each is optimal at least 5% of the 
		time."""
		if kind == 'retro':
			return [ itin for itin in self.retro_itins if itin.prob >= 0.05 ]
		elif kind in ['schedule','sched','s']:
			return [ itin for itin in self.sched_itins if itin.prob >= 0.05 ]

	def get_trips_from_file(self,dataset):
		"""Check files for trips data and read it into a list. Remove any trips
		outside the time window as well as any suboptimal trips."""
		# directories to check
		if dataset == 'sched': 
			directories = ['sched'] 
		elif dataset == 'retro': 
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

	def optimal_departures(self):
		"""Return a set of sampled travel times which are as fast as possible, and 
		indifferent to route choice. This is the status quo."""
		# if we already have it, no need to calculate
		if self.optimal_departures_list:
			return self.optimal_departures_list
		# get all possible trips and any walking alternatives
		departures, all_trips, walk_time = [], [], None
		for itin in self.alter_itins():
			if not walk_time and itin.is_walking: 
				walk_time = itin.walk_time
			else: # itin has transit
				all_trips.extend( itin.get_trips() )
		# if we have only walking, then all trips will be walking
		if walk_time and len(self.alter_itins()) == 1:
			return [ Departure(t,None,walk_time) for t in triptools.sample_times() ]
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
				walk_time and (optimal_trips[i].arrive-time) > walk_time
			) ):
				departures.append( Departure( time, None, walk_time ) )
			# have trip better than walking if that was available
			elif i < len(optimal_trips):
				departures.append( Departure( time, optimal_trips[i] ) )
			# no trip or attractive walking option
			else:
				departures.append( Departure( time ) )
		self.optimal_departures_list = departures
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
		departures, all_trips, walk_time = [], [], None
		# for itineraries sorted in order of mean travel time:
		for itin in sorted(self.alter_itins(),key=lambda i: i.mean_travel_time):
			if not walk_time and itin.is_walking: walk_time = itin.walk_time
			# extend right
			else: all_trips.extend( itin.get_trips() )
		# if we have only walking, then all trips will be walking
		if walk_time and len(self.alter_itins()) == 1:
			return [ Departure(t,None,walk_time) for t in triptools.sample_times() ]
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
				if (not walk_time) or trips[i].first_boarding_time < time + walk_time:
					departures.append( Departure( time, trips[i] ) )
				else: # walking is the better option
					departures.append( Departure( time, None, walk_time ) )
			# no trips left
			else: 
				departures.append( Departure( time, None, walk_time ) )
		return departures

	
	@property
	def sched_entropy(self):
		"""schedule-based entropy"""
		# ensure probabilities sum to 1
		P = [ itin.prob for itin in self.entropy(self.alter_itins('sched')) ]
		P = [ P_i/sum(P) for P_i in P ]
		return - sum( [ P_i * log(P_i,2) for P_i in P ] )

	@property
	def retro_entropy(self):
		"""retro-spective entropy"""
		optimal_paths = [ dep.trip.path for dep in self.optimal_departures() ]
		#get frequency counts
		c = {}
		for path in optimal_paths:
			if path in c:
				c[path] += 1
			else:
				c[path] = 1
		P = [ c[key]/len(optimal_paths) for key in c ]
		return - sum( [ P_i * log(P_i,2) for P_i in P ] )

