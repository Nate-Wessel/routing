# functions involving BD interaction
import psycopg2
import trip, config
from datetime import timedelta

# connect and establish a cursor, based on parameters in conf.py
connection = psycopg2.connect(config.DB_conn)

def cursor():
	"""provide a cursor"""
	return connection.cursor()

def o2d_at(o_stop,d_stop,departure_unix_time):
	"""Return the soonest single-trip connection between two stops."""
	# Query took only 11ms in pgadmin test
	c = cursor()
	c.execute(
		"""
			SELECT 
				--t.trip_id,
				t.route_id,
				--st1.etime AS boarding_time,
				st2.etime AS arrival_time
			FROM ttc_stop_times AS st1
			JOIN ttc_trips AS t 
				ON t.trip_id = st1.trip_id
			JOIN ttc_stop_times AS st2
				ON t.trip_id = st2.trip_id 
			WHERE 
				st1.stop_uid = %(o_stop)s AND
				st1.etime > %(time)s AND
				st2.stop_uid = %(d_stop)s AND
				st1.stop_sequence < st2.stop_sequence -- stops are ordered 
			ORDER BY st1.etime, st2.etime ASC
			LIMIT 1
		""",
		{ 
			'o_stop':int(o_stop), 'd_stop':int(d_stop), 
			'time':int(departure_unix_time) 
		}
	)
	try:
		( route_id, arrival_time ) = c.fetchone()
		return arrival_time, route_id
	except:
		return None, None

def all_itinerary_trips(itin):
	"""Get all trips conforming to a given Itinerary (object instance)"""
	# if that itinerary is just walking, return nothing
	if itin.is_walking: 
		return []
	# query can take more than a second
	c = cursor()
	c.execute("""
		WITH RECURSIVE sub(depth,trips,departure,arrival) AS (
			SELECT 
				1 AS depth,
				ARRAY[t.trip_id] AS trips,
				orig.etime - (%(walk_times)s)[1] AS departure,
				dest.etime + (%(walk_times)s)[2] AS arrival
			FROM ttc_stop_times AS orig
				JOIN ttc_trips AS t
					ON t.trip_id = orig.trip_id
				JOIN ttc_stop_times AS dest
					ON t.trip_id = dest.trip_id 
				WHERE 
					orig.stop_uid = (%(o_stops)s)[1] AND
					dest.stop_uid = (%(d_stops)s)[1] AND
					orig.stop_sequence < dest.stop_sequence AND
					-- departure is within time window
					orig.local_time - '10 minutes'::interval BETWEEN 
						%(window_start)s::time AND 
						%(window_end)s::time + '30 minutes'::interval
						
			UNION
			
			SELECT depth, trips, departure, arrival
			FROM (
				SELECT 
					sub.depth + 1 AS depth,
					sub.trips || t.trip_id AS trips,
					sub.departure,
					dest.etime + (%(walk_times)s)[sub.depth+2] AS arrival,
					row_number() OVER (PARTITION BY sub.trips ORDER BY orig.etime, dest.etime ASC)
				FROM sub, ttc_stop_times AS orig
				JOIN ttc_trips AS t
					ON t.trip_id = orig.trip_id
				JOIN ttc_stop_times AS dest
					ON t.trip_id = dest.trip_id 
				WHERE 
					orig.stop_uid = (%(o_stops)s)[sub.depth+1] AND
					dest.stop_uid = (%(d_stops)s)[sub.depth+1] AND
					orig.etime >= sub.arrival AND
					orig.etime < sub.arrival + 3600 AND
					orig.stop_sequence < dest.stop_sequence
			) AS whatev
			WHERE row_number = 1
		)
		SELECT departure, arrival, trips FROM sub WHERE depth = %(final_depth)s;""",
		{ 
			'o_stops':itin.o_stops,
			'd_stops':itin.d_stops,
			'walk_times':itin.walk_times,
			'final_depth':len(itin.routes),
			'window_start':str(config.window_start_time),
			'window_end':str(config.window_end_time)
		}
	)
	trips = []
	for depart, arrive, trip_ids in c.fetchall():
		trips.append( trip.Trip(depart,arrive,itin.otp_string,trip_ids) )
	return trips


