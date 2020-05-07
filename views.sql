-- views
DROP VIEW IF EXISTS flow_data_view;
CREATE OR REPLACE VIEW flow_data_view  AS
 SELECT a.month,
    a.year,
	a.created,
	a.updated,
    a.report_type,
    c.name AS region,
    b.name AS district,
    c.id AS region_id,
    (b.longitude)::numeric AS longitude,
    (b.latitude)::numeric AS latitude,
    'Malawi'::text AS nation
   FROM flow_data a
     LEFT JOIN locations b ON ((a.district = b.id))
     LEFT JOIN locations c ON ((a.region = c.id));
