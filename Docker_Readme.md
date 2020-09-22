# Getting Started
- Copy the local_settings.py.example to  local_settings.py
- Modify Database section using values from docker compose
- Values can change as long as they are the same in each file.
  - Name is POSTGRES_DB, which is database name
  - User and Password are POSTGRES_USER and POSTGRES_PASSWORD, respectively
  - Host is name of service in docker compose, db in this example
#### docker-compose.yml
```yml
services:
  db:
    image: postgres:alpine
    container_name: postgres_db
    environment:
        - POSTGRES_DB=intake
        - POSTGRES_USER=postgres_user
        - POSTGRES_PASSWORD=postgres_pwdwd
....
```
#### local_settings.py
```json
....
 DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'intake',
        'USER': 'postgres_user',
        'PASSWORD': 'postgres_pwd',
        "HOST" : 'db'
    }
}
....
## Attach to the web server to start Sass watch or to compile.
- Files are linked changes in host directory are changed in the container and vice versa

```
## Commands
- start/stop/rebuild server
```
docker-compose up -d
docker-compose up -d --build
docker-compose down
docker-compose stop
``` 
- -d runs in detached mode, docker finishes
- attach to database
```
 docker exec -it postgres_db psql -U postgres_user -W intake
```
- attach to webserver
  - can run make commands, like 
  - ```make static.dev```
```
 docker exec -it web_server bash
```
- clean up images
```
docker system prune -a 
```

## Troubleshootings
- Sometimes when rebuilding there is an error due to the fact that the linked node_module directory bin has empty files.
  - delete folder and rebuild