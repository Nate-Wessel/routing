CREATE TABLE temp (
	orig_id smallint,
	dest_id smallint,
	a numeric
);
COPY temp FROM '/home/nate/routing/data/test-access.csv' CSV HEADER;

ALTER TABLE ttc_od ADD COLUMN access_12_negexp_45 numeric;
UPDATE ttc_od SET access_12_negexp_45 = a 
FROM temp WHERE dest_id = uid;
DROP TABLE temp;