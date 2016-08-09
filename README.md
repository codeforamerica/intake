# Intake

[![Join the chat at https://gitter.im/codeforamerica/intake](https://badges.gitter.im/codeforamerica/intake.svg)](https://gitter.im/codeforamerica/intake?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Build Status](https://travis-ci.org/codeforamerica/intake.svg?branch=master)](https://travis-ci.org/codeforamerica/intake) [![Test Coverage](https://codeclimate.com/github/codeforamerica/intake/badges/coverage.svg)](https://codeclimate.com/github/codeforamerica/intake/coverage) [![Code Climate](https://codeclimate.com/github/codeforamerica/intake/badges/gpa.svg)](https://codeclimate.com/github/codeforamerica/intake) 
[![Requirements Status](https://requires.io/github/codeforamerica/intake/requirements.svg?branch=master)](https://requires.io/github/codeforamerica/intake/requirements/?branch=master)

## Requirements
To get a local version of intake running, you'll need to have the following installed:
*   [virtualenv](https://github.com/codeforamerica/howto/blob/master/Python-Virtualenv.md)
*   [Node.js and npm](https://github.com/codeforamerica/howto/blob/master/Node.js.md)
*   [Gulp](https://github.com/gulpjs/gulp/blob/master/docs/getting-started.md), simply follow step 1 to enable the `gulp` command from your terminal.
*   [Local PostreSQL](https://github.com/codeforamerica/howto/blob/master/PostgreSQL.md)

## Installation

```
git clone https://github.com/codeforamerica/intake.git
cd intake
virtualenv .
source bin/activate
make install
npm install
```

## Set up the database
With whatever command line interface you're using to interact with your Postgres instance. Creat an intake database:

```
# CREATE DATABASE intake;
```

By default our database owner will have username "postgres" and password="".
To verify this user exists you can use:

```
# SELECT USENAME FROM pg_user;
```

If this user doesn't exist create them with:

```
# CREATE USER postgres PASSSWORD '';
```

## Set up environment variables
To allow Django to deploy onto a localhost, add the following to whatever .__rc file is sourced when you open a terminal (.zshrc, .bashrc, etc.):

```
ALLOWED_HOSTS =  "localhost,127.0.0.1"
```

We're using Sendgrid to handle emails. If you don't have an account it's okay but we still need to set an API_Key. Emails won't work but the app will run. Add the following to the same file as above:

```
SENDGRID_API_KEY = ""
```
If you DO have a Sendgrid account, that's your spot for your api key.

## Run the local server

The following command will spin up a local server at [http://localhost:8000/](http://localhost:8000/)

```
make serve
```

## Testing

To run the suite of integration and unit tests and see a coverage report, use
```
make test
```

### Functional testing

Functional tests are written using the Chrome webdriver with selenium.

Install the Chrome drivers for your operating system. On OS X, you can use Homebrew.

```
brew install chromedriver
brew services start chromedriver
```

Run the functional tests with

```
make test.functional
```

This will create a series of screenshots in `tests/screenshots`.

### Deployment

These instructions assume that the app is being deployed on Heroku with static assets hosted on AWS S3.

