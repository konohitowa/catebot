CREATE TABLE configuration (
	version TEXT,
	username TEXT,
	password TEXT,
	catechismFilename TEXT,
	canonFilename TEXT
);

CREATE TABLE comments (
	id TEXT UNIQUE,
	utc_time INTEGER
);

CREATE TABLE subreddits (
	subreddit TEXT,
	enabled INTEGER
);

CREATE TABLE logs (
	message TEXT,
	type TEXT,
	utc_time INTEGER
);
