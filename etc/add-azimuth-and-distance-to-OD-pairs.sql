CREATE TABLE sampled_ods (
	i int,
	o smallint,
	d smallint,
	azimuth real,
	arc real,
	weight real -- origin area weight X destination area weight
);
COPY sampled_ods (i,o,d) FROM '/home/nate/routing/data/all_sampled_ODs.csv' CSV HEADER;

WITH sub AS (
	SELECT 
		i,o,d,
		degrees( ST_Azimuth( od1.geom::geography, od2.geom::geography ) ) AS az,
		od1.geom::geography <-> od2.geom::geography AS meters,
		ST_Area(od1.voronoi_geom::geography)/10^6 AS o_w, -- square km
		ST_Area(od2.voronoi_geom::geography)/10^6 AS d_w  -- square km
	FROM sampled_ods AS sod 
	JOIN ttc_od AS od1 
		ON o = od1.uid
	JOIN ttc_od AS od2 
		ON d = od2.uid
)
UPDATE sampled_ods SET
	azimuth = az,
	arc = meters,
	weight = o_w * d_w
FROM sub WHERE sub.i = sampled_ods.i;

COPY (
	SELECT * FROM sampled_ods ORDER BY i ASC
) TO '/home/nate/routing/data/all_sampled_ODs_extra.csv' CSV HEADER;



/*
SELECT degrees( ST_Azimuth( 
	ST_Point(0, 0)::geography, 
	ST_Point(-1, 0)::geography 
) )
*/