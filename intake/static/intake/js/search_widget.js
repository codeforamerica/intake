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


  function handleKeypressInSearchInput(e){
    var searchTerm = $(this).val();

    if (event.which == 13 || event.keyCode == 13) {
        //detects an enter keypress, false return prevents form submit
        return false;
    }
    if (searchTerm.length > 0){
      sendSearchQuery(searchTerm);
    } else {
      emptySearchCallback();
    }
  }
  $(inputSelector).on('keypress', "input[name='q']", handleKeypressInSearchInput);
}

module.exports = initializeSearchWidget;