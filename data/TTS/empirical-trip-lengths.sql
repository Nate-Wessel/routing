-- bring in the TTS travel matrix data
CREATE TABLE tts_matrix (
	o smallint,
	d smallint,
	trips smallint
);
COPY tts_matrix FROM '/home/nate/routing/data/TTS/original-OD-flow-matrix.csv' CSV HEADER;

-- measure manhattan distance between TAZ centroids
DROP TABLE IF EXISTS temp2;
WITH sub AS (
	SELECT 
		o,d,trips,
		(t1.centroid <-> t2.centroid) / 1000 AS euclidean, 
		ST_Rotate( ST_MakeLine(t1.centroid,t2.centroid) ,radians(-17), t1.centroid ) AS vect
	FROM tts_matrix
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

-- join taz -> taz trip counts to OD catchment areas
-- TODO this is likely unreasonable - you were tired when you wrote it
WITH sub AS (
	SELECT
		sods.i,
		sum(tm.trips) / (SUM( ST_Area(tz_from.the_geom) + ST_Area(tz_from.the_geom) ) / 1000000) AS trips
	-- join trip counts to TAZs
	FROM tts_matrix AS tm
	JOIN tazs AS tz_from ON tm.o = tz_from.tazid
	JOIN tazs AS tz_to ON tm.d = tz_to.tazid
	-- join tazs to paired OD catchements
	JOIN ttc_od AS od_from ON ST_Intersects(ST_Transform(od_from.voronoi_geom_clipped,26917),tz_from.the_geom) 
	JOIN ttc_od AS od_to ON ST_Intersects(ST_Transform(od_to.voronoi_geom_clipped,26917),tz_to.the_geom) 
	JOIN sampled_ods AS sods ON sods.o = od_from.uid AND sods.d = od_to.uid
	--WHERE sods.i <= 1000
	GROUP BY sods.i
)
UPDATE sampled_ods SET real_flow = trips
FROM sub 
WHERE sampled_ods.i = sub.i