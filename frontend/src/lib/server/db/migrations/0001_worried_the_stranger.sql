ALTER TABLE "User" ADD COLUMN "ucl_api_token" varchar(256);--> statement-breakpoint
ALTER TABLE "User" ADD COLUMN "last_moodle_sync" timestamp with time zone;