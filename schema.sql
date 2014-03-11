drop table if exists entries;
create table entries (
	id integer primary key autoincrement,
	title text not null,
	text text not null,
	my_date text not null,
	version integer not null,
	current boolean not null
);

drop table if exists users;
create table users (
	id integer primary key autoincrement,
	username text not null,
	hpw text not null,
	my_date text not null
);