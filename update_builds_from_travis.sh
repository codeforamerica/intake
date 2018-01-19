if [ "$TRAVIS_EVENT_TYPE" = "push" ]
then
  if [ "$TRAVIS_BRANCH" = "develop" ]
  then
    tower-cli job launch -J 10
  fi
  if [ "$TRAVIS_BRANCH" = "master" ]
  then
    tower-cli job launch -J 24
  fi
fi
