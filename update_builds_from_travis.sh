if [ "$TRAVIS_EVENT_TYPE" = "push" ]
then
  if [ "$TRAVIS_BRANCH" = "develop" ]
  then
    tower-cli job launch -J 10 # staging
  fi
  if [ "$TRAVIS_BRANCH" = "master" ]
  then
    tower-cli job launch -J 25 # demo
    tower-cli job launch -J 24 # production
  fi
fi
