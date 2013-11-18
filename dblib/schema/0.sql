-- Initial schema.  Subject to changing often and nowhere near to being 
-- finalized, so I'll save revision 1.sql for after the first stable release.
-- For now, table upgrades will have to be done by hand.

CREATE TABLE IF NOT EXISTS "_meta" 
	("key" text NOT NULL PRIMARY KEY, "int_value" int, "str_value" text);

CREATE TABLE IF NOT EXISTS "users"
	("id" SERIAL PRIMARY KEY, "name" text, "surname" text, 
	"email" text, "salt" text, "hash" VARCHAR(256), 
	"home_phone" text, "mobile_phone" text, 
	"sms_capable" boolean DEFAULT FALSE, "dob" DATE, 
	"license_number" text, "email_verified" boolean DEFAULT FALSE, 
	"newsletter" boolean DEFAULT FALSE, "admin" boolean DEFAULT FALSE, 
	"join_date" timestamp DEFAULT NOW(),
	"last_login" timestamp, "last_seen" timestamp, 
	"last_updated" timestamp, "locked" boolean DEFAULT FALSE); 
	
CREATE TABLE IF NOT EXISTS "services"
	("id" SERIAL PRIMARY KEY, "name" text NOT NULL, 
	"day" INT CHECK (day >= 0 AND day <= 7), 
	start_time TIME WITHOUT TIME ZONE NOT NULL, 
	end_time TIME WITHOUT TIME ZONE NOT NULL); 
	
CREATE TABLE IF NOT EXISTS "activities"
	("id" SERIAL PRIMARY KEY, "name" text UNIQUE NOT NULL, 
	"admin" INT DEFAULT 1 REFERENCES users(id) ON DELETE SET DEFAULT); 
	
CREATE TABLE IF NOT EXISTS "barcode"
	("id" SERIAL PRIMARY KEY, "value" text NOT NULL, 
	"person" INT REFERENCES users(id) ON DELETE CASCADE); 
	
CREATE TABLE IF NOT EXISTS "user_openid"
	("id" SERIAL PRIMARY KEY, "identity" text UNIQUE NOT NULL, 
	"person" INT REFERENCES users(id) ON DELETE CASCADE); 
	
CREATE TABLE IF NOT EXISTS "statistics"
	("id" SERIAL PRIMARY KEY, 
	"person" INT DEFAULT 1 REFERENCES users(id) ON DELETE SET DEFAULT, 
	"checkin" timestamp, "checkout" timestamp,
	"service" text[], "activity" text[], "note" text); 

-- Default user referenced by the statistics table, if record is deleted:
INSERT INTO "users" (id, name, surname, locked, join_date, hash) VALUES
	(1, 'Deleted', 'User', TRUE, NOW(), 'disabled');
UPDATE "users" SET "name" = 'Deleted', "surname" = 'User', locked = TRUE,
	join_date = NOW(), hash = 'disabled' WHERE id = 1;

INSERT INTO "_meta"("key", "int_value") VALUES ('schema_version', 0);
UPDATE "_meta" SET "int_value" = 0 WHERE "key" = 'schema_version';
INSERT INTO "_meta"("key", "int_value") VALUES ('require_version', 0);
UPDATE "_meta" SET "int_value" = 0 WHERE "key" = 'require_version';

INSERT INTO "_meta"("key", "str_value") VALUES ('site_title', 'DreamTeam Check-in');
UPDATE "_meta" SET "str_value" = 'DreamTeam Check-in' WHERE "key" = 'site_title';

--kiosk strings and messages:
-- kiosk_search_message
INSERT INTO "_meta"("key", "str_value") VALUES ('kiosk_search_message', 
'Welcome.  To begin, type the last four digits of your phone number or your last name.');
UPDATE "_meta" SET "str_value" = 
'Welcome.  To begin, type the last four digits of your phone number or your last name.'
WHERE "key" = 'kiosk_search_message';

-- kiosk_results_message
INSERT INTO "_meta"("key", "str_value") VALUES ('kiosk_results_message', 
'Select your name from the list below, or press <strong>go back</strong> to search again.');
UPDATE "_meta" SET "str_value" = 
'Select your name from the list below, or press <strong>go back</strong> to search again.'
WHERE "key" = 'kiosk_results_message';

-- kiosk_activity_title
INSERT INTO "_meta"("key", "str_value") VALUES ('kiosk_activity_title', 'Select Activity');
UPDATE "_meta" SET "str_value" = 'Select Activity' WHERE "key" = 'kiosk_activity_title';
-- checkboxes or radiobuttons for the activity selection? (default: checkboxes)
INSERT INTO "_meta"("key", "str_value") VALUES ('kiosk_activity_allow_multiple', 't');
UPDATE "_meta" SET "str_value" = 't' WHERE "key" = 'kiosk_activity_allow_multiple';

-- kiosk_service_title
INSERT INTO "_meta"("key", "str_value") VALUES ('kiosk_service_title', 'Select Services');
UPDATE "_meta" SET "str_value" = 'Select Services' WHERE "key" = 'kiosk_service_title';
-- checkboxes or radiobuttons for the service selection? (default: checkboxes)
INSERT INTO "_meta"("key", "str_value") VALUES ('kiosk_service_allow_multiple', 't');
UPDATE "_meta" SET "str_value" = 't' WHERE "key" = 'kiosk_service_allow_multiple';

-- Check-in note title (e.g. 'Prayer Request')
INSERT INTO "_meta"("key", "str_value") VALUES ('kiosk_note_title', 'Check-in Note');
UPDATE "_meta" SET "str_value" = 'Check-in Note' WHERE "key" = 'kiosk_note_title';

-- timeout function will automatically go back to the search page if the session
-- is idle for more than n seconds: (default 30).  Set to 0 or less to disable.
INSERT INTO "_meta"("key", "int_value") VALUES ('kiosk_timeout', 30);
UPDATE "_meta" SET "int_value" = 30 WHERE "key" = 'kiosk_timeout';
-- Show a warning dialog when the countdown reaches n (15). negative to disable.
INSERT INTO "_meta"("key", "int_value") VALUES ('kiosk_timeout_warning', 15);
UPDATE "_meta" SET "int_value" = 30 WHERE "key" = 'kiosk_timeout';

-- Timeout warning message: (NULL for the template default)
INSERT INTO "_meta"("key", "str_value") VALUES ('kiosk_timeout_message', NULL);
UPDATE "_meta" SET "str_value" = NULL WHERE "key" = 'kiosk_timeout_message';

-- Timeout warning dialogue title: (NULL for the template default)
INSERT INTO "_meta"("key", "str_value") VALUES ('kiosk_timeout_title', NULL);
UPDATE "_meta" SET "str_value" = NULL WHERE "key" = 'kiosk_timeout_title';
