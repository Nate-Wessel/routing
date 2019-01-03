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

#def itinerary_trips()
