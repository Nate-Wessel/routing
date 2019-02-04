CREATE TABLE temp (
	orig_id smallint,
	dest_id smallint,
	ah numeric,
	aa numeric,
	ic smallint,
	en numeric
);
COPY temp FROM '/home/nate/routing/data/test-access.csv' CSV HEADER;

--ALTER TABLE ttc_od ADD COLUMN entropy numeric;

UPDATE ttc_od SET 
	access_habit = ah,
	access_any = aa,
	itin_count = ic,
	entropy = en
FROM temp WHERE dest_id = uid;
DROP TABLE temp;
