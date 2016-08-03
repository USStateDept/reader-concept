-- create table for documents
drop table if exists document;

create table document (
  id integer primary key autoincrement,
  uid text not null,
  u_date text not null,
  doc_date text not null,
  addressee text not null,
  classification text not null,
  category text not null,
  from_bur text not null,
  from_auth text not null,
  title text not null,
  full_text text not null,
  html text not null,
  doc_path text not null,
  has_attachments integer not null,
  attach_urls text,
  approved_bur text,
  approved_name text,
  draft_bur text,
  draft_name text,
  draft_ext text,
  draft_phone text,
  clear_blob text,
  top_terms text
);

-- create table for similarity scores
-- each document pair will be represented in both orientations,
-- in order to streamline retrieval
-- composite key allows for flexible re-computing of similarity scores
drop table if exists similar;

create table similar (
  uid_1 text not null,
  uid_2 text not null,
  score float not null,
  primary key (uid_1, uid_2)
);

drop table if exists user;

create table user (
  pid text not null primary key,
  fname text not null,
  lname text not null,
  uname text not null,
  phash text not null,
  psalt text not null
);

-- {pid} takes {action} on {rid} (resource id) at {datetime}
-- running ledger of events
drop table if exists user_actions;

create table user_actions (
  pid text not null,
  action text not null,
  rid text not null,
  datetime text not null
)