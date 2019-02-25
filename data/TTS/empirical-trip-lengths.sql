/*
CREATE TABLE temp (
	o smallint,
	d smallint,
	trips smallint
);
COPY temp FROM '/home/nate/routing/data/TTS/original-OD-flow-matrix.csv' CSV HEADER;
*/
DROP TABLE IF EXISTS temp2;


WITH sub AS (
	SELECT 
		o,d,trips,
		(t1.centroid <-> t2.centroid) / 1000 AS euclidean, 
		ST_Rotate( ST_MakeLine(t1.centroid,t2.centroid) ,radians(-17), t1.centroid ) AS vect
	FROM temp 
	JOIN tazs AS t1 ON o = t1.tazid
	JOIN tazs AS t2 ON d = t2.tazid
)
SELECT 
	o,d,trips,euclidean,
	(ABS(ST_X(ST_StartPoint(vect))-ST_X(ST_EndPoint(vect))) + 
	ABS(ST_Y(ST_StartPoint(vect))-ST_Y(ST_EndPoint(vect))))/1000 AS grid_dist
INTO temp2
FROM sub;

COPY (
	SELECT * FROM temp2
) TO '/home/nate/routing/data/TTS/observed_trip_lengths.csv' CSV HEADER;

--ALTER TABLE tazs ADD COLUMN centroid geometry(Point,26917);
--UPDATE tazs SET centroid = ST_Centroid(the_geom)
