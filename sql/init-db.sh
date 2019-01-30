export PGUSER="${POSTGRES_USER}"

psql <<- EOSQL
	CREATE DATABASE homework;
	\c homework
	CREATE EXTENSION IF NOT EXISTS timescaledb;
	CREATE TABLE cpu_usage(
	  ts    TIMESTAMPTZ,
	  host  TEXT,
	  usage DOUBLE PRECISION
	);
	SELECT create_hypertable('cpu_usage', 'ts');
EOSQL

psql homework <<- EOSQL
	\COPY cpu_usage FROM '/docker-entrypoint-initdb.d/cpu_usage.csv' WITH DELIMITER ',' CSV HEADER;
EOSQL
