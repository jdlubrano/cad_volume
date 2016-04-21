SELECT a.file, p.id, p.width, p.length, p.thickness, p.diameter
  FROM parts p, assets a
  WHERE p.id = a.owner_id AND a.owner_type = 'Part' AND (a.file ILIKE '%.stp' OR a.file ILIKE '%.step');
