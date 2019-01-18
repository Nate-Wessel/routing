from trip import Trip
import os, csv, time
import datetime as dt
from math import log
import config, db
from misc import clip_trips_to_window, remove_premature_departures
from itinerary import Itinerary

class OD(object):
	"""An O->D pair"""
	def __init__(self,origin,dest):
		"""origin and dest are integer IDs"""
		self.orig = origin
		self.dest = dest
		# read in the trip itineraries
		self.retro_trips = self.get_trips_from_file('retro')
		self.sched_trips = self.get_trips_from_file('sched')
		self.allocate_time(self.sched_trips)
		self.allocate_time(self.retro_trips)
		# summarize itinerary data
		self.sched_itins = self.summarize_itineraries(self.sched_trips)
		self.retro_itins = self.summarize_itineraries(self.retro_trips)

	def __repr__(self):
		name = str(self.orig)+' -> '+str(self.dest)
		sched = '\n\tsched | entropy:{} | trips:{}'.format( 
			round(self.sched_entropy,2), len(self.sched_trips) )
		retro = '\n\tretro | entropy:{} | trips:{}'.format( 
			round(self.retro_entropy,2), len(self.retro_trips) )
		for i in [0,1,2]:
			sched += '\n\t\tPr:{}, '.format( round(self.sched_itin_p(i),3) )
			retro += '\n\t\tPr:{}, '.format( round(self.retro_itin_p(i),3) )
			sched += 'It:{}'.format( self.sched_itin(i) )
			retro += 'It:{}'.format( self.retro_itin(i) ) 
		return( name + sched + retro )

	def get_alt_trips(self):
		"""testing..."""
		# get top three retro itineraries
		pass

	def allocate_time(self,trips):
		"""Allocate the time (in seconds) for which this trip is the next, 
		clipping to the window used for removing trips."""
		# sort the trips by departure
		trips = sorted(trips, key=lambda k: k.depart) 
		dates_seen = set()
		for i, trip in enumerate(trips):
			if i == 0 or not trip.depart.date() in dates_seen:
				# trip is first of the day
				dates_seen |= {trip.depart.date()}
				# create a localized datetime 
				start_dt = dt.datetime.combine(
					trip.depart.date(), 
					config.window_start_time
				)
				start_dt = config.tz.localize( start_dt )
				from_prev = (trip.depart - start_dt).total_seconds()
			else:
				# trip follows previous trip on this day 
				from_prev = (trip.depart - trips[i-1].depart).total_seconds()
			trip.time_before = from_prev
				
	def entropy(self,itineraries):
		"""shannon entropy of the itinerary probability distribution"""
		entropy = 0
		for itin in itineraries:
			entropy += itin['prob'] * log(itin['prob'],2)
		return - entropy

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
		clip_trips_to_window(trips)
		remove_premature_departures(trips)
		return trips
		
	def summarize_itineraries(self,trips):
		"""Returns a list of itineraries sorted by prominence. Total time within 
		the time window spent as optimal next trip is assigned to itineraries as 
		a property."""
		# get a set of distinct itinerary objects
		unique_itins = set([trip.itinerary for trip in trips])
		# put this in a dict with initial counts
		counter = { it:{'time':0,'count':0} for it in unique_itins }
		# add times from trips to each 
		for trip in trips:
			counter[trip.itinerary]['time'] += trip.time_before
			counter[trip.itinerary]['count'] += 1
		# for each itinerary and it's counts
		for it in counter:
			it.time = counter[it]['time']
			it.count = counter[it]['count']
		# we now reconstruct this from the dict as a list of itineraries
		unique_itins =  [ it for it in counter ]
		# get total time in trips
		total_time = sum( [ it.time for it in unique_itins ] )
		# assign probabilities based on share of total time
		for it in unique_itins:
			it.prob = it.time / total_time
		# and sort by prob, highest first
		return sorted( unique_itins, key=lambda k: k.prob, reverse=True )

	def access(self,kind='habitual'):
		"""return a vector of minutely travel times based on the given 
		accessibility metric"""
		if kind in ['habitual','h','H']:
			# route choice is based on whatever is generally the best
			# no deviation from that route
			if not self.retro_itin(0).is_walking: # don't look up a walking trip
				trips = db.all_itinerary_trips(self.retro_itin(0))
				clip_trips_to_window(trips)
				return trips
			else:
				return []
		else: 
			print('invalid access type supplied')
			assert False

	# here be some simplifying properties/methods
	
	@property
	def sched_entropy(self):
		"""schedule-based entropy"""
		return self.entropy(self.sched_itins)
	@property
	def retro_entropy(self):
		"""retro-spective entropy"""
		return self.entropy(self.retro_itins)

	def sched_itin(self,i):
		"""scheduled itinerary at the given index if any"""
		return self.sched_itins[i] if i < len(self.sched_itins) else None
	def retro_itin(self,i):
		"""scheduled itinerary at the given index if any"""
		return self.retro_itins[i] if i < len(self.retro_itins) else None

	def sched_itin_p(self,i):
		"""scheduled itinerary probability at the given index if any"""
		return self.sched_itins[i]['prob'] if i < len(self.sched_itins) else 0
	def retro_itin_p(self,i):
		"""scheduled itinerary probability at the given index if any"""
		return self.retro_itins[i]['prob'] if i < len(self.retro_itins) else 0
	

