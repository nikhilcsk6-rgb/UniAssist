CREATE DATABASE IF NOT EXISTS uniassist CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE uniassist;

CREATE TABLE roles (
  id TINYINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(20) NOT NULL UNIQUE
);
INSERT INTO roles (name) VALUES ('student'),('faculty'),('admin');

CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  role_id TINYINT NOT NULL,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  department VARCHAR(100),
  preferred_language ENUM('en','kn','hi') DEFAULT 'en',
  theme ENUM('light','dark') DEFAULT 'light',
  is_active TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (role_id) REFERENCES roles(id),
  INDEX idx_users_role (role_id)
);

CREATE TABLE documents (
  id INT PRIMARY KEY AUTO_INCREMENT,
  owner_id INT NOT NULL,
  title VARCHAR(255) NOT NULL,
  original_filename VARCHAR(255) NOT NULL,
  stored_filename VARCHAR(255) NOT NULL,
  file_type ENUM('pdf','docx','txt') NOT NULL,
  category ENUM('official','study_material','personal') NOT NULL DEFAULT 'personal',
  visibility ENUM('public','private') NOT NULL DEFAULT 'private',
  page_count INT DEFAULT 0,
  chunk_count INT DEFAULT 0,
  status ENUM('uploaded','indexed','failed') DEFAULT 'uploaded',
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_docs_owner (owner_id),
  INDEX idx_docs_category (category, visibility)
);

CREATE TABLE chat_sessions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  title VARCHAR(200) DEFAULT 'New chat',
  mode ENUM('university','document','study') DEFAULT 'university',
  document_id INT NULL,
  language ENUM('en','kn','hi') DEFAULT 'en',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL,
  INDEX idx_sessions_user (user_id, created_at)
);

CREATE TABLE chat_messages (
  id INT PRIMARY KEY AUTO_INCREMENT,
  session_id INT NOT NULL,
  sender ENUM('user','assistant') NOT NULL,
  content MEDIUMTEXT NOT NULL,
  sources JSON NULL,
  response_time_ms INT NULL,
  grounded TINYINT(1) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
  INDEX idx_msgs_session (session_id, created_at)
);

CREATE TABLE generated_questions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  document_id INT NULL,
  question_type ENUM('mcq','short','long','true_false') NOT NULL,
  marks TINYINT NULL,
  difficulty ENUM('easy','medium','difficult') NOT NULL,
  question_text TEXT NOT NULL,
  options JSON NULL,
  answer_key TEXT NOT NULL,
  paper_id VARCHAR(40) NULL,
  paper_title VARCHAR(200) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL,
  INDEX idx_gq_user (user_id), INDEX idx_gq_paper (paper_id)
);

CREATE TABLE quizzes (
  id INT PRIMARY KEY AUTO_INCREMENT,
  creator_id INT NOT NULL,
  document_id INT NULL,
  title VARCHAR(200) NOT NULL,
  difficulty ENUM('easy','medium','difficult') DEFAULT 'medium',
  questions JSON NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
);

CREATE TABLE quiz_results (
  id INT PRIMARY KEY AUTO_INCREMENT,
  quiz_id INT NOT NULL,
  user_id INT NOT NULL,
  score INT NOT NULL,
  total INT NOT NULL,
  answers JSON NULL,
  taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_qr_user (user_id)
);

CREATE TABLE announcements (
  id INT PRIMARY KEY AUTO_INCREMENT,
  author_id INT NOT NULL,
  title VARCHAR(200) NOT NULL,
  body TEXT NOT NULL,
  category ENUM('exam','event','holiday','deadline','circular','general') DEFAULT 'general',
  audience ENUM('all','student','faculty') DEFAULT 'all',
  event_date DATE NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_ann_cat (category, created_at)
);

CREATE TABLE feedback (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  message_id INT NULL,
  type ENUM('rating','incorrect_report','suggestion') NOT NULL,
  rating TINYINT NULL CHECK (rating BETWEEN 1 AND 5),
  comment TEXT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE SET NULL,
  INDEX idx_fb_type (type)
);

CREATE TABLE benchmark_items (
  id INT PRIMARY KEY AUTO_INCREMENT,
  dataset_name VARCHAR(120) NOT NULL,
  question TEXT NOT NULL,
  reference_answer TEXT NOT NULL,
  reference_document VARCHAR(255) NULL,
  reference_page INT NULL,
  uploaded_by INT NOT NULL,
  FOREIGN KEY (uploaded_by) REFERENCES users(id),
  INDEX idx_bench_ds (dataset_name)
);

CREATE TABLE research_experiments (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(160) NOT NULL,
  dataset_name VARCHAR(120) NOT NULL,
  llm_model VARCHAR(80) NOT NULL,
  temperature DOUBLE NOT NULL,
  top_k TINYINT NOT NULL,
  is_sample TINYINT(1) NOT NULL DEFAULT 0,  -- 1 = illustrative sample, 0 = measured
  status ENUM('pending','running','completed','failed') DEFAULT 'pending',
  created_by INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE evaluation_metrics (
  id INT PRIMARY KEY AUTO_INCREMENT,
  experiment_id INT NOT NULL,
  benchmark_item_id INT NOT NULL,
  model_variant ENUM('A_no_rag','B_rag') NOT NULL,
  generated_answer MEDIUMTEXT,
  accuracy_score DOUBLE,
  relevance_score DOUBLE,
  hallucinated TINYINT(1),
  response_time_ms INT,
  abstained TINYINT(1) DEFAULT 0,
  citation_correct TINYINT(1) NULL,
  retrieval_precision DOUBLE NULL,
  FOREIGN KEY (experiment_id) REFERENCES research_experiments(id) ON DELETE CASCADE,
  FOREIGN KEY (benchmark_item_id) REFERENCES benchmark_items(id) ON DELETE CASCADE,
  INDEX idx_em_exp (experiment_id, model_variant)
);

CREATE TABLE activity_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NULL,
  action VARCHAR(80) NOT NULL,
  details JSON NULL,
  ip_address VARCHAR(45),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_log_user (user_id), INDEX idx_log_action (action, created_at)
);
