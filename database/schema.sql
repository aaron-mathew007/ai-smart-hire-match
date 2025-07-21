CREATE TABLE resumes (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL
);

CREATE TABLE job_descriptions (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL
);

CREATE TABLE match_scores (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    score FLOAT NOT NULL
);
