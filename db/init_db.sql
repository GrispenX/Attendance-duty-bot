CREATE DATABASE IF NOT EXISTS bot;
use bot;

CREATE TABLE IF NOT EXISTS `users` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  `surname` varchar(255) NOT NULL,
  `telegram_id` bigint UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS `roles` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  `user_id` integer NOT NULL,
  `role` varchar(255) NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS `subjects` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `is_active` bool NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS `lessons` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  `subject_id` integer NOT NULL,
  `index` integer NOT NULL,
  `date` date NOT NULL,
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

CREATE TABLE IF NOT EXISTS `attendance` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  `lesson_id` integer NOT NULL,
  `user_id` integer NOT NULL,
  `status` enum('present','formal_present','unpresent') NOT NULL,
  FOREIGN KEY (lesson_id) REFERENCES lessons(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS `duties` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  `date` date NOT NULL,
  `status` enum('done','undone') NOT NULL
);

CREATE TABLE IF NOT EXISTS `duty_assignments` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  `duty_id` integer NOT NULL,
  `user_id` integer NOT NULL,
  FOREIGN KEY (duty_id) REFERENCES duties(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS `groups` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  `telegram_id` bigint NOT NULL
);

CREATE TABLE IF NOT EXISTS `duty_photos` (
  `id` integer PRIMARY KEY AUTO_INCREMENT,
  `user_id` integer NOT NULL,
  `duty_id` integer NOT NULL,
  `photo` longblob NOT NULL,
  FOREIGN KEY (duty_id) REFERENCES duties(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

INSERT INTO users (surname, telegram_id) VALUES ('Ковальчук', 578368948);
INSERT INTO roles (user_id, `role`) VALUES (1, 'admin');
INSERT INTO roles (user_id, `role`) VALUES (1, 'superadmin');