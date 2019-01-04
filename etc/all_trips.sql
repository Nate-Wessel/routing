--14,58,1510032686,1510034354,"{w196,s6027,r96,s6039,w51,s2109,r37,s2011,w55}"

WITH RECURSIVE sub(depth,it,trips,routes,departure,arrival) AS (

	SELECT 
		0 AS depth,
		'{w196,s6027,r96,s6039,w51,s2109,r37,s2011,w55}'::text[] AS it,
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
			st1.stop_uid = substring( (
				'{w196,s6027,r96,s6039,w51,s2109,r37,s2011,w55}'::text[]
			)[2],2)::int 
			AND
			st2.stop_uid = substring((
				'{w196,s6027,r96,s6039,w51,s2109,r37,s2011,w55}'::text[]
			)[4],2)::int 
			AND
			st1.stop_sequence < st2.stop_sequence -- stops are ordered 
			
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
			st1.stop_sequence < st2.stop_sequence -- stops are ordered 
	) AS whatev
	WHERE row_number = 1
)
SELECT 
	trips,
	routes,
	departure,
	arrival
FROM sub
WHERE depth = 2;