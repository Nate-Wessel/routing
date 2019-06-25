/*
CREATE TABLE sampled_ods (
	i int,
	o smallint,
	d smallint,
	azimuth real,
	arc real,
	o_area real,
	d_area real,
	grid_dist real,
	real_flow real,
	o_km_from_sub real,
	d_km_from_sub real,
	crosses_sub boolean;
);
COPY sampled_ods (i,o,d) FROM '/home/nate/routing/data/all_sampled_ODs.csv' CSV HEADER;
*/

WITH sub AS (
	SELECT 
		i,o,d,
		degrees( ST_Azimuth( od1.geom::geography, od2.geom::geography ) ) AS az,
		(od1.geom::geography <-> od2.geom::geography) / 1000 AS km,
		ST_Area(od1.voronoi_geom::geography)/10^6 AS o_sqkm, -- square km
		ST_Area(od2.voronoi_geom::geography)/10^6 AS d_sqkm, -- square km
		ST_Rotate( ST_MakeLine(od1.loc_geom,od2.loc_geom) ,radians(-17), od1.loc_geom ) AS v
	FROM sampled_ods AS sod 
	JOIN ttc_od AS od1 
		ON o = od1.uid
	JOIN ttc_od AS od2 
		ON d = od2.uid
)
UPDATE sampled_ods SET
	azimuth = az,
	arc = km,
	o_area = o_sqkm,
	d_area = d_sqkm,
	grid_dist = (ABS(ST_X(ST_StartPoint(v))-ST_X(ST_EndPoint(v))) + ABS(ST_Y(ST_StartPoint(v))-ST_Y(ST_EndPoint(v))))/1000
FROM sub WHERE sub.i = sampled_ods.i;

/*
WITH sub AS (
	SELECT 
		t.uid, min( t.loc_geom <-> ST_Transform(s.geom,32617) ) /1000 AS min_dist
	FROM ttc_od AS t, subways AS s
	GROUP BY t.uid
)
UPDATE sampled_ods SET d_km_from_sub = min_dist
FROM sub
WHERE sampled_ods.d = sub.uid
*/

COPY (
	SELECT  
		i,o,d,
		azimuth,arc,o_area,d_area,
		grid_dist,o_km_from_sub,d_km_from_sub,
		crosses_sub,real_flow
	FROM sampled_ods ORDER BY i ASC
	--LIMIT 10000
) TO '/home/nate/routing/data/sampled-ODs/all.csv' CSV HEADER;