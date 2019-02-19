# This is for getting detailed stats on a single OD, mainly for diagnostic tests
from OD import OD

oid = 12
did = 316
od = OD(oid,did)
print( od )

# get the departures and arrivals for the top trips and put them in a CSV

# write all trips for the top itineraries to a file
with open('data/untracked/db-trips.csv','w') as outfile:
	outfile.write('depart,arrive,itinerary')
	for itin in od.alter_itins():
		for trip in itin.get_trips():
			outfile.write( '\n{},{},"{}"'.format(
				trip.depart_ts, trip.arrive_ts, itin 
			) )
