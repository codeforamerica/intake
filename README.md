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