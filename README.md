# Intake

[![Join the chat at https://gitter.im/codeforamerica/intake](https://badges.gitter.im/codeforamerica/intake.svg)](https://gitter.im/codeforamerica/intake?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Build Status](https://travis-ci.org/codeforamerica/intake.svg?branch=master)](https://travis-ci.org/codeforamerica/intake) [![Test Coverage](https://codeclimate.com/github/codeforamerica/intake/badges/coverage.svg)](https://codeclimate.com/github/codeforamerica/intake/coverage) [![Code Climate](https://codeclimate.com/github/codeforamerica/intake/badges/gpa.svg)](https://codeclimate.com/github/codeforamerica/intake) 
[![Requirements Status](https://requires.io/github/codeforamerica/intake/requirements.svg?branch=master)](https://requires.io/github/codeforamerica/intake/requirements/?branch=master)

## Requirements
To get a local version of intake running, you'll need to have the following installed:
*   [python 3.5](https://github.com/codeforamerica/howto/blob/master/Python-Virtualenv.md) (note that python 3.5 includes `venv`, a standard library module. Separate installation of virtualenv is unnecessary)
*   [Node.js 7.4 and npm](https://github.com/codeforamerica/howto/blob/master/Node.js.md)
*   [Gulp](https://github.com/gulpjs/gulp/blob/master/docs/getting-started.md), simply follow step 1 to enable the `gulp` command from your terminal.
*   [Local PostreSQL](https://github.com/codeforamerica/howto/blob/master/PostgreSQL.md)

## Installation and Setup

### Quickstart

An overview of the command line steps to get started
```sh
git clone https://github.com/codeforamerica/intake.git
cd intake
createdb intake
cp ./local_settings.py.example ./local_settings.py
# add database connection info to local_settings.py
python3 -m venv .
source bin/activate
make install
./manage.py collectstatic
make db.setup  # migrate the database and add seed data
make serve   # run the server
```

### Installation

Be sure to install all the dependencies in a python virtual environment. `make install` will install both npm packages as well as python packages.

```sh
git clone https://github.com/codeforamerica/intake.git
cd intake
python3 -m venv .  # or virtualenv .
source bin/activate
make install
```

### Copy the local settings

```sh
cp ./local_settings.py.example ./local_settings.py
```


### Set up the database

Make sure you have a local PostgreSQL database, and that you know the login information. Add this database information to `local_settings.py`. If you're not sure how to setup a PostgreSQL database, [read more documentation]([Local PostreSQL](https://github.com/codeforamerica/howto/blob/master/PostgreSQL.md)) before proceeding.

For example, if I have a default user named `postgres`:

```sh
# create a database named "intake"
createdb intake
```

```python
# in local_settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'intake',
        'USER': 'postgres',
    }
}
```


With the database connection information in place, the following command will migrate the database and add seed data:

```sh
make db.setup
```


### Build static assets

This only needs to be run the first time you set up.

```sh
./manage.py collectstatic
```

## Run the local server

The following command will spin up a local server at [http://localhost:8000/](http://localhost:8000/)

```sh
make serve
```

## Testing

To run the test suite, use:
```sh
make test
```


If you'd like to see coverage results you can use:
```sh
make test.coverage
```

Some of the tests take longer to run than others. Some of them need to create and read pdfs on the file system. These do not run local by default. But they do run during Travis builds. If you'd like to include these slower tests you can run them with:

```sh
make test.deluxe
```

To target a particular test, you can add a `SCOPE` variable. For example if I want to just test that an org user can only see applications to their own organization on the app index page, I would run:
```sh
make test \
    SCOPE=intake.tests.views.test_admin_views.TestApplicationIndex.test_that_org_user_can_only_see_apps_to_own_org
```

Alternatively you could run all the tests for the admin views with:

```sh
make test \
    SCOPE=intake.tests.views.test_admin_views
```

As you can see, the `SCOPE` variable should use the syntax of a python import path.

## Debugging and introspection

The requirements include a few libraries that are helpful for debugging and exploring functionality.


### `ipdb` breakpoints
To set an interactive breakpoint somewhere in the code, insert this line:

```python
import ipdb; ipdb.set_trace()
```

[Here is a Sublime Text snippet](https://gist.github.com/bengolder/f18d7aa10d3119381ead2a4b3ca7247a) that lets you type `ipd` as shortcut for the line above. Go to _Tools > Developer > New Snippet_ while a python file is open.

The execution will enter an interactive prompt at this point in the code, with tab completion and a variety of shortcuts available.

- **`s` or `step`**: step into the next execution frame.
- **`c` or `continue`**: Continue exection
- **`u` or `up`**: Move up one frame in the stack trace.
- **`d` or `down`**: Move down one frame in the stack trace.
- **`n` or `next`**: continue to the next line.
- **`ll`**: show the lines of code in the current function.
- **`pp`**: pretty print an object. For example, (`pp my_object`).

### `shell_plus` interactive python shell

To load an interactive ipython prompt with tab completion, models, and other useful things preloaded, run this shell command:

```sh
./manage.py shell_plus
```

Any print commands will pretty print by default. Tab completion is available.


## Static Asset Handling

Here is the step-by-step process for static asset handling:

1. Static assets start in the `frontend/` folder.
2. gulp & browserify are used to bundle javascript modules from `frontend/js/` into `frontend/build/js/`.
2. gulp & less are used to bundle `frontend/less` into `frontend/build/css`.
3. gulp also copies image files into the build folder. For example `frontend/img` into `frontend/build/img`.
4. When running the local dev server, gulp watches for changes to `less` and `.js` files, and overwrites `frontend/build` with any updates to the bundled assets.
4. The `frontend/build/` folder is overwritten by gulp. Don't try to edit the files it contains.
5. `frontend/build/` is also included in the git repo, unfortunately. Once our deployment environment can pull in frontend libraries and run gulp to bundle frontend assets, we can remove this folder from git.
5. Django's builtin `./manage.py collectstatic` command copies files from `frontend/build` and other django app static directories (such as `django/contrib/admin/static/admin`) and copies them into `project/static`. Heroku runs this command with every deployment.
6. In production, [WhiteNoise](http://whitenoise.evans.io/en/stable/) serves static files from the `project/static` folder.

In sum, here are the files and folders essential to static asset handling:
- `frontend/build` <sup>(tracked by git)</sup>, a folder that is overwritten by gulp. Do not edit it's contents directly.
- `gulpfile.js` <sup>(tracked by git)</sup>, a file containing all the tasks used to build frontend assets
- `frontend/js` and `frontend/less` <sup>(tracked by git)</sup>, where the javascript modules and less files live.
- `project/static` <sup>(_not_ tracked by git)</sup>, overwritten by `./manage.py collectstatic` and used to serve static files in production.
