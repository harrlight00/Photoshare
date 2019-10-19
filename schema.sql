CREATE DATABASE photoshare;
USE photoshare;
DROP TABLE Pictures CASCADE;
DROP TABLE Users CASCADE;
DROP TABLE Friend CASCADE;
DROP TABLE Tag CASCADE;
DROP TABLE Comments CASCADE;
DROP TABLE Album CASCADE;
DROP TABLE Likes CASCADE;

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT NOT NULL,
    email varchar(255) UNIQUE NOT NULL,
    password varchar(255) NOT NULL,
	firstname varchar(255) NOT NULL,
	lastname varchar(255) NOT NULL,
	birthday date NOT NULL,
	hometown varchar(255),
	gender enum('Male','Female', 'Other'),
	profilepic longblob,
	bio varchar(255),
	CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Likes (
	picture_id int4 NOT NULL,
	user_id int4 NOT NULL,
	INDEX picid_idx (picture_id),
	CONSTRAINT likes_pk PRIMARY KEY (user_id, picture_id)
);
	
CREATE TABLE Pictures (
  picture_id int4  AUTO_INCREMENT NOT NULL,
  user_id int4 NOT NULL,
  imgdata longblob NOT NULL,
  caption VARCHAR(255) NOT NULL,
  album_id int4 NOT NULL,
  INDEX upid_idx (user_id),
  INDEX aid_idx (album_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id)
);

CREATE TABLE Friend (
  user_id int4 NOT NULL,
  friend_id int4 NOT NULL,
  INDEX upid_idx (user_id),
  CONSTRAINT friend_pk PRIMARY KEY (user_id, friend_id)
);

CREATE TABLE Tag (
  picture_id int4 NOT NULL,
  tag varchar(255) NOT NULL,
  INDEX pid_idx (picture_id),
  INDEX tag_idx (tag),
  CONSTRAINT tag_pk PRIMARY KEY (tag, picture_id)
);

CREATE TABLE Comments (
  comment_id int4  AUTO_INCREMENT NOT NULL,
  user_id int4 NOT NULL,
  picture_id int4 NOT NULL,
  dateofC date NOT NULL,
  text VARCHAR(255) NOT NULL,
  INDEX upid_idx (user_id),
  INDEX pid_idx (picture_id),
  CONSTRAINT comment_pk PRIMARY KEY (comment_id)
);

CREATE TABLE Album (
  album_id int4  AUTO_INCREMENT NOT NULL,
  user_id int4 NOT NULL,
  dateofC date NOT NULL,
  name VARCHAR(255) NOT NULL,
  INDEX upid_idx (user_id),
  INDEX upalb_idx (user_id, name),
  CONSTRAINT album_pk PRIMARY KEY (album_id)
  );