CREATE TABLE sampled_ods (
	i int,
	o smallint,
	d smallint,
	azimuth real,
	arc real,
	o_area real,
	d_area real,
	grid_dist real
);
COPY sampled_ods (i,o,d) FROM '/home/nate/routing/data/all_sampled_ODs.csv' CSV HEADER;

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

COPY (
	SELECT * FROM sampled_ods ORDER BY i ASC
	--LIMIT 10000
) TO '/home/nate/routing/data/sampled-ODs/all.csv' CSV HEADER;



/*
SELECT degrees( ST_Azimuth( 
	ST_Point(0, 0)::geography, 
	ST_Point(-1, 0)::geography 
) )
*/