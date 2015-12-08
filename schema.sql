drop table if exists players;
create table players (
  id integer primary key autoincrement,
  name text not null,
  wins integer not null,
  losses integer not null,
  rating real not null
);

create table games (
  id integer primary key autoincrement,
  time_entered integer not null,
  red_player_one integer not null,
  red_player_two integer not null,
  blue_player_one integer not null,
  blue_player_two integer not null,
  red_score integer not null,
  blue_score integer not null
);
