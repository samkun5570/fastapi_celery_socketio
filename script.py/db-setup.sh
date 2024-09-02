#!/bin/sh

export PGUSER="postgres"
psql -c "CREATE DATABASE IF NOT EXISTS fastApiTddDb"
psql fastApiTddDb -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"