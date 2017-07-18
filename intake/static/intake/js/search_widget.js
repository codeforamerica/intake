function initializeSearchWidget(inputSelector, postURL, resultsCallback, emptySearchCallback){
  var currentXHR = null;

  function handleResultsAndResetRequest(callback){
    return function(results){
      callback(results);
      currentXHR = null;
    };
  }

  function sendSearchQuery(searchTerm){
      var data = {'q': searchTerm};
      // abort any existing request
      if (currentXHR){ currentXHR.abort(); }
      currentXHR = $.post(
        postURL, data, handleResultsAndResetRequest(resultsCallback)
      ).fail(function(jqXHR){
          if(jqXHR.status == 403){
            location.reload();
          }
        }
      );
  }


  function handleKeyupInSearchInput(e){
    var searchTerm = $(this).val();

    if (searchTerm.length > 0){
      sendSearchQuery(searchTerm);
    } else {
      emptySearchCallback();
    }
  }
  $(inputSelector).on('keyup', "input[name='q']", handleKeyupInSearchInput);
}

module.exports = initializeSearchWidget;