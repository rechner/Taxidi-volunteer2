-- Initial schema.  Subject to changing often and nowhere near to being 
-- finalized, so I'll save revision 1.sql for after the first stable release.
-- For now, table upgrades will have to be done by hand.

CREATE TABLE IF NOT EXISTS "_meta" 
	("key" text NOT NULL PRIMARY KEY, "int_value" int, "str_value" text);

CREATE TABLE IF NOT EXISTS "users"
	("id" SERIAL PRIMARY KEY, "name" text, "surname" text, 
	"email" text, "salt" text, "hash" VARCHAR(256), 
	"home_phone" text, "mobile_phone" text, "sms_capable" boolean, 
	"dob" DATE, "license_number" text, "email_verified" boolean, 
	"newsletter" boolean, "admin" boolean, "join_date" timestamp, 
	"last_login" timestamp, "last_seen" timestamp, 
	"last_updated" timestamp, "locked" boolean); 
	
CREATE TABLE IF NOT EXISTS "services"
	("id" SERIAL PRIMARY KEY, "name" text, 
	"day" INT CHECK (day >= 0 AND day <= 7), 
	start_time TIME WITHOUT TIME ZONE, end_time TIME WITHOUT TIME ZONE); 
	
CREATE TABLE IF NOT EXISTS "activities"
	("id" SERIAL PRIMARY KEY, "name" text UNIQUE NOT NULL, 
	"admin" INT REFERENCES users(id) ON DELETE RESTRICT); 
	
CREATE TABLE IF NOT EXISTS "barcode"
	("id" SERIAL PRIMARY KEY, "value" text UNIQUE NOT NULL, 
	"person" INT REFERENCES users(id) ON DELETE CASCADE); 
	
CREATE TABLE IF NOT EXISTS "user_openid"
	("id" SERIAL PRIMARY KEY, "identity" text UNIQUE NOT NULL, 
	"person" INT REFERENCES users(id) ON DELETE CASCADE); 
	
CREATE TABLE IF NOT EXISTS "statistics"
	("id" SERIAL PRIMARY KEY, "person" INT REFERENCES users(id), 
	"checkin" timestamp, "checkout" timestamp,
	"service" text[], "activity" text, "note" text); 
	

INSERT INTO "_meta"("key", "int_value") VALUES ('schema_version', 0);
UPDATE "_meta" SET "int_value" = 0 WHERE "key" = 'schema_version';
INSERT INTO "_meta"("key", "int_value") VALUES ('require_version', 0);
UPDATE "_meta" SET "int_value" = 0 WHERE "key" = 'require_version';

INSERT INTO "_meta"("key", "str_value") VALUES ('site_title', 'DreamTeam');
UPDATE "_meta" SET "str_value" = 'DreamTeam' WHERE "key" = 'site_title';


