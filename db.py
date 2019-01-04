# functions involving BD interaction
import psycopg2

# connect and establish a cursor, based on parameters in conf.py
conn_string = (
	"host='localhost' dbname='diss_access' user='nate' password='mink'" )
connection = psycopg2.connect(conn_string)
connection.autocommit = True

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
	"""Get all trips conforming to a given itinerary.
	Itineraries should be given as postgresql array literals.
	e.g. '{w196,s6027,r96,s6039,w51,s2109,r37,s2011,w55}'"""
	walk_speed = 2 # meters / second
	# query can take more than a second
	c = cursor()
	c.execute(
		"""
			WITH RECURSIVE sub(depth,it,trips,routes,departure,arrival) AS (

				SELECT 
					0 AS depth,
					%(it)s::text[] AS it,
					ARRAY[t.trip_id] AS trips,
					ARRAY[t.route_id] AS routes,
					st1.etime AS departure,
					st2.etime AS arrival_time
				FROM ttc_stop_times AS st1
					JOIN ttc_trips AS t
						ON t.trip_id = st1.trip_id
					JOIN ttc_stop_times AS st2
						ON t.trip_id = st2.trip_id 
					WHERE 
						st1.stop_uid = substring( (%(it)s::text[])[2],2)::int AND
						st2.stop_uid = substring((%(it)s::text[])[4],2)::int AND
						st1.stop_sequence < st2.stop_sequence
						
				UNION
				
				SELECT depth, it, trips, routes, departure, arrival
				FROM (
					SELECT 
						sub.depth+1 AS depth,
						sub.it AS it,
						sub.trips || t.trip_id AS trips,
						sub.routes || t.route_id::varchar AS routes,
						sub.departure,
						st2.etime AS arrival,
						row_number() OVER (PARTITION BY sub.trips ORDER BY st1.etime, st2.etime ASC)
					FROM sub, ttc_stop_times AS st1
					JOIN ttc_trips AS t
						ON t.trip_id = st1.trip_id
					JOIN ttc_stop_times AS st2
						ON t.trip_id = st2.trip_id 
					WHERE 
						st1.stop_uid = substring(sub.it[2+4*depth],2)::int AND
						st1.etime >= sub.arrival AND
						st1.etime < sub.arrival + 3600 AND
						st2.stop_uid = substring(sub.it[4+4*depth],2)::int AND
						st1.stop_sequence < st2.stop_sequence
				) AS whatev
				WHERE row_number = 1
			)
			SELECT trips, routes, departure, arrival
			FROM sub
			WHERE depth = 2;
		""", { 'it':itin }
	)
	return c.fetchall()
