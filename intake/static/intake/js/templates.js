function renderTagAutocompleteResultTemplate(result){
  var activeClass = result.selected ? ' active' : '';
  return '<li class="autocomplete-result'+activeClass+'">'+result.prefix+'<span class="result-match">'+result.selection+'</span>'+result.suffix+'</li>';
}

function renderTagTemplate(tag){
  return '<span class="tag label" data-key="'+tag.id+'"">' +
    '<span class="tag-text">'+tag.name+'</span> ' +
    '<span class="tag-remove glyphicon glyphicon-remove-sign" title="Remove this tag"></span>' +
  '</span> ';
}

function renderNoteTemplate(note){
	return '<div class="note" data-key="'+note.id+'">' +
    '<div class="note-time">'+note.created+'</div>' +
    '<div class="note-body">'+note.body+'</div>' +
    '<div class="note-author">-'+note.user+'</div>' +
    '<div class="note-remove" title="Delete this note">' +
      '<button class="btn btn-danger btn-sm">' +
      '<span class="glyphicon glyphicon-remove-sign"></span> Delete</a>' +
    '</div>' +
  '</div>';
}

function renderApplicationSearchResult(searchResult){
  var activeClass = searchResult.selected ? ' active' : '';
  return '<li class="autocomplete-result'+activeClass+'"><a href="'+searchResult.url+'">'+searchResult.name+'</a></li>';
}

module.exports = {
  tag: renderTagTemplate,
  tagAutocompleteSearchResult: renderTagAutocompleteResultTemplate,
  note: renderNoteTemplate,
  searchResult: renderApplicationSearchResult,
}