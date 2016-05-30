# Intake

[![Build Status](https://travis-ci.org/codeforamerica/intake.svg?branch=master)](https://travis-ci.org/codeforamerica/intake) [![Test Coverage](https://codeclimate.com/github/codeforamerica/intake/badges/coverage.svg)](https://codeclimate.com/github/codeforamerica/intake/coverage) [![Code Climate](https://codeclimate.com/github/codeforamerica/intake/badges/gpa.svg)](https://codeclimate.com/github/codeforamerica/intake) 
[![Requirements Status](https://requires.io/github/codeforamerica/intake/requirements.svg?branch=master)](https://requires.io/github/codeforamerica/intake/requirements/?branch=master)

## Installation

```
git clone https://github.com/codeforamerica/intake.git
cd intake
source bin/activate
make install
```

## Set up the database


## Set up environmental variables


## Run the local server

The following command will spin up a local server at [http://localhost:5000/](http://localhost:5000/)

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

