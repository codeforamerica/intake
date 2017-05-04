var $ = require('jquery');
var templates = require('./templates');


function sendSearchQuery(searchTerm){
    var searchUrl = '/applicant-autocomplete/?q=' + searchTerm;
    $.get(searchUrl, handleSearchResults
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
		renderSearchResults([])
	}
}

function renderSearchResults(parsedResults){
	$('ul.applicants-autocomplete_results').html(
		parsedResults.map(templates.searchResult).join('')
	)
}

function handleSearchResults(jsonResponse){
	var parsedResults = jsonResponse.results.map(function(result){
		return result.id;
	});
	renderSearchResults(parsedResults);
}

function initSearchWidgets(){
  var widgets = $('.applicants-search_module');
  widgets.on('keyup', "input[name='q']", handleKeyupInSearchInput);
}

module.exports = {
  init: initSearchWidgets,
};