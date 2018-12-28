import requests, multiprocessing, time, os, csv, sys
from datetime import datetime, timedelta
from random import shuffle

# where are the things?
output_dir	= '/home/nate/dissdata/routing/sched/'
OD_file		= 'ODs.csv'
OTP_server	= 'http://166.48.61.19:8080/otp/routers/ttc-sched/plan'

# define the start time
start_time = datetime( year=2017, month=11, day=10 )
print('from ',start_time)
# and go for how long?
end_time = start_time + timedelta(hours=24)
print('until',end_time)

# how many processors to use?
num_procs = 6

# difference from server time zone in seconds
TZdiff = 3600 * 0

# read in the OD location data
points = {}
with open(OD_file) as csvfile:
	reader = csv.DictReader(csvfile, delimiter=',')
	for r in reader:
		points[int(r['uid'])] = {'lat':float(r['lat']),'lon':float(r['lon'])}

# read in the selected set of OD's to analyze
OD_pairs = []
with open('1k_od_sample.csv') as csvfile:
	reader = csv.DictReader(csvfile, delimiter=',')
	for r in reader:
		# skip if the results already exist
		if not os.path.exists(output_dir+r['o']+'/'+r['d']+'.csv'):
			OD_pairs.append( (int(r['o']),int(r['d'])) )
#OD_pairs = [(365,363)]
print(len(OD_pairs),'pairs to work on')
shuffle(OD_pairs)




def calc_od(od_tuple):
	"""calculate all shortest itineraries for this OD pair in the time 
		period of interest"""
	function_start_time = time.time() # for timing the function
	# get the OD geometries
	oid,did = od_tuple
	print('starting',oid,'->',did)
	o,d = points[oid], points[did]
	# define the static OTP routing parameters
	options = {
		'mode':'TRANSIT,WALK',
		'maxWalkDistance':2000, # meters
		'wheelchair':'false',
		'arriveBy':'false', # meaning departAt 
		'maxTransfers':2,
		'numItineraries':1,
		#'transferPenalty':5*60, # five minutes
		#'walkReluctance':1.2,
		#'waitReluctance':2,
		'fromPlace':( str(o['lat'])+','+str(o['lon']) ),
		'toPlace':( str(d['lat'])+','+str(d['lon']) )
		#'reverseOptimizeOnTheFly': 'true'
	}
	# start at the start time
	t = start_time 
	# results dictionary, keyed by arrival times
	trips = {}
	while t <= end_time:
		#print oid, did, t, len(trips)
		# set the time of this query
		options['date'] = t.strftime('%m-%d-%Y')
		options['time'] = t.strftime('%I:%M%p')
		# make the request
		response = requests.get( OTP_server, params=options )
		try:
			result = response.json()
		except:
			print('json error at',t,response.text)
			t += timedelta(minutes=5)
			continue 
		# check for errors
		if 'error' in result:
			# print an error message
			print(oid,'-->',did,' -- ',result['error']['message'],'at',t) 
			# then add a good chunk of time before trying again
			t += timedelta(minutes=10)
			continue
		# now we have an actual result from the router
		itinerary = result['plan']['itineraries'][0]
		# get details of the route
		legs = summarize_legs(itinerary)
		# overwrite any previous trip that may have had the same arrival time
		# time from milliseconds to seconds and clip to nearest second
		departure = int( itinerary['startTime'] / 1000.0 ) + TZdiff
		arrival = int( itinerary['endTime'] / 1000.0 ) + TZdiff
		# in case we have this time already, we need to switch to the slower, 
		# more optimized method to save time on future requests
		if arrival in trips and not 'reverseOptimizeOnTheFly' in options:
			options['reverseOptimizeOnTheFly'] = 'true'
			print('\toptimizing on-the-fly')
		# and store the result
		trips[arrival] = { 'departure':departure, 'itinerary':legs }
		# in case this is a walk only result, increment by more than a minute
		# or we'll be here all day
		if len(itinerary['legs']) == 1 and itinerary['legs'][0]['mode'] == 'WALK':
			t = datetime.fromtimestamp(departure) + timedelta(minutes=10)
		else:
			# set the next request for just after the last departure time given here
			t = datetime.fromtimestamp(departure) + timedelta(minutes=1)
	# save the output
	write_output(trips,oid,did)
	# let us know what's going on
	print( oid,'->',did,'took',round(time.time()-function_start_time,2),'& found',len(trips) )


def summarize_legs(itinerary):
	"""returns a short array summary of the trip to be saved in the DB"""
	legs = []
	for leg in itinerary['legs']:
		# is it a walking leg?
		if leg['mode'] == 'WALK':
			# show that we're walking and how far
			legs.append('w'+str(int(leg['distance'])))
		# or is it a transit leg?
		elif 'route' in leg:
			# add both stops and the route number
			orig_stop = 's'+ leg['from']['stopId'][2:] # remove the '1:'
			dest_stop = 's'+ leg['to']['stopId'][2:]   # remove the '1:'
			if len(legs) == 0 or legs[-1] != orig_stop: 
				legs.append( orig_stop ) 
			legs.append( 'r'+ leg['route'] )
			legs.append( dest_stop ) 
		else:
			print(response.url)
	return legs

def write_output(trips,oid,did):
	"""after all the results are in, output a file, even an empty one to show 
	that the work is done. store results in folders named after origins, 
	files named after destinations"""
	if not os.path.exists(output_dir+str(oid)):
		os.makedirs(output_dir+str(oid))
	with open(output_dir+str(oid)+'/'+str(did)+'.csv','w+') as outfile:
		outfile.write('o,d,depart,arrive,itinerary')
		# now we're going to sort by the keys (arrival times)
		arrival_times = list(trips.keys())
		arrival_times.sort()
		for arrival in arrival_times:
			outfile.write(
				'\n'+str(oid)+','+str(did)+','+
				# cast these to datetime
				str(trips[arrival]['departure'])+','+str(arrival)+','+
				# format as a postgresql array literal
				'"{'+','.join(trips[arrival]['itinerary'])+'}"' 
			)

# create the process pool
pool = multiprocessing.Pool(num_procs)
# and get it started
pool.map(calc_od,OD_pairs,chunksize=1)

print('COMPLETED!')


