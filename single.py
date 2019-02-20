# This is for getting detailed stats on a single OD, mainly for diagnostic tests
from OD import OD
import triptools

oid = 12
did = 316
od = OD(oid,did)
print( od )

# get the travel times for the top itineraries and put them in a CSV

# column names
col_names = list('abcdefghijklmnopqrstuvwxyz')

# write all trips for the top itineraries to a file
with open('data/output/12->316-trips.csv','w') as outfile:
	# first identify the itineraries
	outfile.write('Itineraries:\n')
	# enumerate itinerary alternatives
	for i, itin in enumerate(od.alter_itins()):
		outfile.write('{}: {}\n'.format(col_names[i],itin))
	# give a linebreak and start the CSV
	header = '\ndepart,'+','.join( col_names[0:len(od.alter_itins())] )
	outfile.write(header)
	unformatted_row = '\n'+','.join( ['{}'] * ( 1 + len( od.alter_itins() ) ) )
	# build out a 2d list of travel times for each itinerary
	travel_times = []
	for itin in od.alter_itins():
		trips = itin.get_trips()
		travel_times.append(triptools.trips2times(trips))
	# for each departure time, print the travel times
	for depth, departure in enumerate(travel_times[0]):
		times = [ str(itin[depth].minutes_travel) for itin in travel_times ]
		outfile.write( '\n'+str(departure.unix_departure)+','+','.join(times) )
