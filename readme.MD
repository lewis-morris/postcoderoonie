postgres user 

postcodes 


indexes for speed 

CREATE INDEX idx_income ON places (postcode ASC, postcode_trim ASC);
CREATE INDEX idx_postcode ON places (postcode ASC, postcode_trim ASC);
CREATE INDEX idx_postcode_gin ON places USING gin (postcode gin_trgm_ops);
