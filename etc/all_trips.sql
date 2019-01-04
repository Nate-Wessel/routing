--14,58,1510032686,1510034354,"{w196,s6027,r96,s6039,w51,s2109,r37,s2011,w55}"

WITH RECURSIVE sub(depth,trips,routes,arrival_time,it) AS (

	SELECT 
		0 AS depth,
		NULL::text[] AS trips,
		NULL::text[] AS routes,
		1510032686::double precision AS arrival_time,
		'{w196,s6027,r96,s6039,w51,s2109,r37,s2011,w55}'::text[] AS it		
		
	UNION
	
	SELECT depth, trips, routes, arrival_time, it 
	FROM (
		SELECT 
			sub.depth+1 AS depth,
			sub.trips || t.trip_id::text AS trips,
			sub.routes || t.route_id::text AS routes,
			st2.etime AS arrival_time,
			sub.it AS it,
			row_number() OVER (PARTITION BY sub.trips ORDER BY st1.etime, st2.etime ASC)
		FROM sub, ttc_stop_times AS st1
		JOIN ttc_trips AS t
			ON t.trip_id = st1.trip_id
		JOIN ttc_stop_times AS st2
			ON t.trip_id = st2.trip_id 
		WHERE 
			st1.stop_uid = substring(sub.it[2+4*depth],2)::int AND
			st1.etime >= sub.arrival_time AND
			st1.etime < sub.arrival_time + 3600 AND
			st2.stop_uid = substring(sub.it[4+4*depth],2)::int AND
			st1.stop_sequence < st2.stop_sequence -- stops are ordered 
	) AS whatev
	WHERE row_number = 1
)
SELECT * 
FROM sub 
LIMIT 100;