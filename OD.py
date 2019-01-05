from trip import Trip
import os, csv
import datetime as dt
from math import log
from pytz import timezone
input_dir = '/home/nate/dissdata/routing/'

# define time window to clip to 
start = dt.time(6,30,0) # h,m,s; 6:30am
end = dt.time(22,0,0) # h,m,s;  10:00pm

EST = timezone('America/Toronto')

class OD(object):
	"""An O->D pair"""
	def __init__(self,origin,dest):
		"""origin and dest are dictionaries of the values from the ODs.csv file"""
		self.orig = origin
		self.dest = dest
		# read in the trip itineraries
		self.retro_trips = self.get_all_trips('retro')
		self.sched_trips = self.get_all_trips('sched')
		# clean out irrelevant trips for both datasets
		self.remove_trips_outside_window()
		self.remove_suboptimal_trips()
		self.allocate_time(self.sched_trips)
		self.allocate_time(self.retro_trips)
		# summarize itinerary data
		self.sched_itins = self.summarize_itineraries(self.sched_trips)
		self.retro_itins = self.summarize_itineraries(self.retro_trips)
		# print summary info, including entropy
		print(self)
		for trip in self.retro_trips:
			trip.verify()

	def __repr__(self):
		name = self.orig['nomen']+' -> '+self.dest['nomen']
		sched = '\n\tsched | entropy:{}'.format( round(self.sched_entropy,2) )
		retro = '\n\tretro | entropy:{}'.format( round(self.retro_entropy,2) )
		for i in [0,1,2]:
			sched += '\n\t\tPr:{}, '.format( round(self.sched_itin_p(i),3) )
			retro += '\n\t\tPr:{}, '.format( round(self.retro_itin_p(i),3) )
			sched += 'It:{}'.format( self.sched_itin(i) )
			retro += 'It:{}'.format( self.retro_itin(i) ) 
		return( name + sched + retro )

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
				start_dt = dt.datetime.combine(trip.depart.date(), start)
				start_dt = EST.localize( start_dt )
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

	def get_all_trips(self,dataset):
		"""Check files for trips data and read it into a list."""
		# directories to check
		if dataset == 'sched': 
			directories = ['sched'] 
		elif dataset == 'retro': 
			directories = ['17476','17477','17478','17479','17480']
		trips = []
		for d in directories:
			csvpath = input_dir+d+'/'+self.orig['uid']+'/'+self.dest['uid']+'.csv'
			if not os.path.exists(csvpath): continue			
			with open(csvpath) as f:
				reader = csv.DictReader(f)	
				trips.extend( 
					[ Trip(r['depart'],r['arrive'],r['itinerary']) for r in reader ]
				)
		return trips

	def remove_trips_outside_window(self):
		"""clip to trips inside a defined daytime window"""
		for trips in [self.sched_trips,self.retro_trips]:
			to_remove = []
			for i, trip in enumerate(trips):
				if trip.arrive.time() > end or trip.depart.time() < start:
					to_remove.append(i)
			for i in reversed(to_remove):
				del trips[i]
			#print('\t',len(to_remove),'trips removed from window')

	def remove_suboptimal_trips(self):
		"""If a trip departs earlier but gets in later than another trip it is 
		suboptimal and needs to be removed. Do this for both scheduled and 
		retrospective trips."""
		for trips in [self.sched_trips,self.retro_trips]:
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
			print('\t',starting_length - len(trips),'suboptimal trips removed')
		
	def summarize_itineraries(self,trips):
		"""proportions of fastest trip itineraries"""
		# get distinct itineraries
		itins = set([trip.itin_uid for trip in trips])
		# put this in a dict with initial counts
		itins = { key:{'itin':key,'time':0,'count':0} for key in itins }
		# add times from trips to each 
		for trip in trips:
			itins[trip.itin_uid]['time'] += trip.time_before
			itins[trip.itin_uid]['count'] += 1
		# change format from dict to list of dicts
		itins = [ itins[i] for i in itins ]
		# assign probabilities based on share of total time
		total_time = sum( [ i['time'] for i in itins ] )
		for i in itins: i['prob'] = i['time'] / total_time
		# and sort by prob, highest first
		itins = sorted(itins, key=lambda k: k['prob'],reverse=True) 
		return itins

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
	

