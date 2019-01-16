from trip import Trip
import os, csv
import datetime as dt
from math import log
import config, db

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
		self.clip_trips_to_window(trips)
		self.remove_premature_departures(trips)
		return trips

	def clip_trips_to_window(self,trips):
		"""Remove trips outside a defined time window (set in config.py)."""
		to_remove = []
		for i, trip in enumerate(trips):
			if ( 
				trip.arrive.time() > config.window_end_time or 
				trip.depart.time() < config.window_start_time 
			):
				to_remove.append(i)
		for i in reversed(to_remove):
			del trips[i]
		#print('\t',len(to_remove),'trips removed from window')

	def remove_premature_departures(self,trips):
		"""If a trip departs earlier but gets in later than another trip it is 
		suboptimal and needs to be removed."""
		starting_length = len(trips)
		# Sort by arrival, then search for trips not also sorted by departure
		trips.sort(key = lambda x: x.arrive_ts) # arrival, first to last
		fully_sorted = False # starting assumption
		while not fully_sorted:
			for i, trip in enumerate(trips):
				# if departure is before that of earlier-arriving trip
				if i > 0 and trip.depart_ts <= trips[i-1].depart_ts:
					trips.pop(i)
					continue
			fully_sorted = True 
		#print('\t',starting_length - len(trips),'suboptimal trips removed')
		
	def summarize_itineraries(self,trips):
		"""proportions of fastest trip itineraries"""
		# get distinct itineraries
		itins = set([trip.itinerary for trip in trips])
		# put this in a dict with initial counts
		itins = { key:{'itin':key,'time':0,'count':0} for key in itins }
		# add times from trips to each 
		for trip in trips:
			itins[trip.itinerary]['time'] += trip.time_before
			itins[trip.itinerary]['count'] += 1
		# change format from dict to list of dicts
		itins = [ itins[i] for i in itins ]
		# assign probabilities based on share of total time
		total_time = sum( [ i['time'] for i in itins ] )
		for i in itins: i['prob'] = i['time'] / total_time
		# and sort by prob, highest first
		itins = sorted(itins, key=lambda k: k['prob'],reverse=True) 
		return itins

	def access(self,kind='habitual'):
		"""return a vector of minutely travel times based on the given 
		accessibility metric"""
		if kind in ['habitual','h','H']:
			# route choice is based on whatever is generally the best
			# no deviation from that route
			if not self.retro_itin(0).is_walking: # don't look up a walking trip
				trips = db.all_itinerary_trips(self.retro_itin(0))
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
		return self.sched_itins[i]['itin'] if i < len(self.sched_itins) else ''
	def retro_itin(self,i):
		"""scheduled itinerary at the given index if any"""
		return self.retro_itins[i]['itin'] if i < len(self.retro_itins) else ''

	def sched_itin_p(self,i):
		"""scheduled itinerary probability at the given index if any"""
		return self.sched_itins[i]['prob'] if i < len(self.sched_itins) else 0
	def retro_itin_p(self,i):
		"""scheduled itinerary probability at the given index if any"""
		return self.retro_itins[i]['prob'] if i < len(self.retro_itins) else 0
	

