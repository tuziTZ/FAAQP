BEGIN;

DROP TABLE IF EXISTS movie_keyword;
DROP TABLE IF EXISTS movie_companies;
DROP TABLE IF EXISTS movie_info;
DROP TABLE IF EXISTS movie_info_idx;
DROP TABLE IF EXISTS cast_info;
DROP TABLE IF EXISTS title CASCADE;

CREATE TABLE title (
    id integer NOT NULL,
    title character varying,
    imdb_index character varying,
    kind_id integer NOT NULL,
    production_year integer,
    imdb_id character varying,
    phonetic_code character varying,
    episode_of_id integer,
    season_nr integer,
    episode_nr integer,
    series_years character varying,
    md5sum character varying,
    CONSTRAINT title_pkey PRIMARY KEY (id)
);

CREATE TABLE cast_info (
    id integer NOT NULL,
    person_id integer,
    movie_id integer NOT NULL,
    person_role_id integer,
    note text,
    nr_order integer,
    role_id integer NOT NULL,
    CONSTRAINT cast_info_pkey PRIMARY KEY (id),
    CONSTRAINT cast_info_movie_id_fkey FOREIGN KEY (movie_id) REFERENCES title(id)
);

CREATE TABLE movie_companies (
    id integer NOT NULL,
    movie_id integer NOT NULL,
    company_id integer,
    company_type_id integer,
    note text,
    CONSTRAINT movie_companies_pkey PRIMARY KEY (id),
    CONSTRAINT movie_companies_movie_id_fkey FOREIGN KEY (movie_id) REFERENCES title(id)
);

CREATE TABLE movie_info (
    id integer NOT NULL,
    movie_id integer NOT NULL,
    info_type_id integer NOT NULL,
    info text,
    note text,
    CONSTRAINT movie_info_pkey PRIMARY KEY (id),
    CONSTRAINT movie_info_movie_id_fkey FOREIGN KEY (movie_id) REFERENCES title(id)
);

CREATE TABLE movie_info_idx (
    id integer NOT NULL,
    movie_id integer NOT NULL,
    info_type_id integer NOT NULL,
    info text,
    note text,
    CONSTRAINT movie_info_idx_pkey PRIMARY KEY (id),
    CONSTRAINT movie_info_idx_movie_id_fkey FOREIGN KEY (movie_id) REFERENCES title(id)
);

CREATE TABLE movie_keyword (
    id integer NOT NULL,
    movie_id integer NOT NULL,
    keyword_id integer NOT NULL,
    CONSTRAINT movie_keyword_pkey PRIMARY KEY (id),
    CONSTRAINT movie_keyword_movie_id_fkey FOREIGN KEY (movie_id) REFERENCES title(id)
);

\copy title FROM '/workspace/FAAQP/imdb-benchmark-1k/postgres_clean/title.csv' WITH (FORMAT csv, NULL '');
\copy cast_info FROM '/workspace/FAAQP/imdb-benchmark-1k/postgres_clean/cast_info.csv' WITH (FORMAT csv, NULL '');
\copy movie_companies FROM '/workspace/FAAQP/imdb-benchmark-1k/postgres_clean/movie_companies.csv' WITH (FORMAT csv, NULL '');
\copy movie_info FROM '/workspace/FAAQP/imdb-benchmark-1k/postgres_clean/movie_info.csv' WITH (FORMAT csv, NULL '');
\copy movie_info_idx FROM '/workspace/FAAQP/imdb-benchmark-1k/postgres_clean/movie_info_idx.csv' WITH (FORMAT csv, NULL '');
\copy movie_keyword FROM '/workspace/FAAQP/imdb-benchmark-1k/postgres_clean/movie_keyword.csv' WITH (FORMAT csv, NULL '');

CREATE INDEX idx_cast_info_movie_id ON cast_info USING btree (movie_id);
CREATE INDEX idx_movie_companies_movie_id ON movie_companies USING btree (movie_id);
CREATE INDEX idx_movie_info_movie_id ON movie_info USING btree (movie_id);
CREATE INDEX idx_movie_info_idx_movie_id ON movie_info_idx USING btree (movie_id);
CREATE INDEX idx_movie_keyword_movie_id ON movie_keyword USING btree (movie_id);

COMMIT;
