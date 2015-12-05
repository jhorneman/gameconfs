# Local database to Heroku

    pg_dump --host localhost --port 5432 --username "gameconfs" -Fc --no-acl --no-owner --verbose --file "/Users/jhorneman/Desktop/data.dump" "gameconfs"

    heroku pg:backups restore 'http://www.intelligent-artifice.com/data.dump' DATABASE -a gameconfs --confirm gameconfs

# Heroku database to local

    heroku pg:backups capture && curl -o latest.dump `heroku pg:backups public-url`

Source: [https://devcenter.heroku.com/articles/heroku-postgres-backups]

    pg_restore --verbose --clean --no-acl --no-owner --host localhost --port 5432 --username "gameconfs" --dbname "gameconfs" latest.dump

The user is important! See: [http://www.softr.li/blog/2012/07/25/postgresql-schema-owner-altered-during-dump-prevent-access-from-rails]

### Create local database from scratch

    CREATE USER "gdcal-dev" WITH PASSWORD "<password>";
    CREATE DATABASE "gdcal-dev";
    GRANT ALL PRIVILEGES ON DATABASE "gdcal-dev" to "gdcal-dev";

#### List backups on Heroku

    heroku pg:backups
