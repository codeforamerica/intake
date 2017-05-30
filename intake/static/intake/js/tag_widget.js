var $ = require('jquery');
var tagSearch = require('./tag_search');
var templates = require('./templates');
var ajaxModule = require('./ajax');


// key codes
var UP_ARROW = 38;
var DOWN_ARROW = 40;
var TAB_KEY = 9;
var DELETE_KEY = 8;


// there is one STATE used for any active widget
var STATE;
function resetState(){
  // revert to initial state
  STATE = {
    elems: {
      widget: null,
      input: null,
      resultsList: null
    },
    results: [],
    selectedResultIndex: null,
  };
}

function clearResults(){
  // empty all results and render an empty menu
  STATE.results = [];
  renderResults();
}

function selectResult(index){
  /*
    changes the state to select the new result (by index)
    and then renders the new results state
  */
  var currentIndex = STATE.selectedResultIndex;
  if( currentIndex !== null ){
    var currentSelection = STATE.results[currentIndex];
    currentSelection.selected = false;
  }
  STATE.selectedResultIndex = index;
  if( index !== null ){
    STATE.results[index].selected = true
  }
  renderResults();
}

function renderResults(){
  // render the menu to match the search results state
  STATE.elems.resultsList.html(
    STATE.results.map(templates.tagAutocompleteSearchResult).join('')
  );
}

function getMaxSplittingIndex(text){
  // get the index position after the last comma or space
  var lastCommaIndex = text.lastIndexOf(',');
  return Math.max(lastCommaIndex) + 1;
}


function updateAutocompleteSearchWithLatestValue(){
  // get the portion of text after the last comma or space
  var currentValue = STATE.elems.input.val();
  var maxCuttingIndex = getMaxSplittingIndex(currentValue);
  var searchTerm = currentValue.substring(maxCuttingIndex);
  STATE.results = tagSearch.searchTags(searchTerm);
  if( STATE.results.length > 0){
    selectResult(0);
  } else {
    renderResults();
  }
}

function selectPreviousResult(){
  var currentIndex = STATE.selectedResultIndex;
  switch( currentIndex ){
    case null:
      // if nothing is selected, select the last result
      selectResult(STATE.results.length - 1);
      break;
    case 0:
      // if the first result is selected, clear the selection
      selectResult(null);
      break;
    default:
      // select the result before the current one
      selectResult(currentIndex - 1);
      break;
  }
  renderResults();
}

function selectNextResult(){
  var currentIndex = STATE.selectedResultIndex;
  var lastResultIndex = STATE.results.length - 1;
  switch( currentIndex ){
    case null:
      // if nothing is selected, select the first result
      selectResult(0);
      break;
    case lastResultIndex:
      // if the last result is selected, select the first result
      selectResult(0);
      break;
    default:
      // select the result after the current one
      selectResult(currentIndex + 1);
      break;
  }
}

function addSelectedResult(){
  /*
    appends the current result selection to the input's value
    replacing any half-typed tag names
  */
  var currentValue = STATE.elems.input.val();
  var currentResult = STATE.results[STATE.selectedResultIndex];
  var maxCuttingIndex = getMaxSplittingIndex(currentValue);
  var existingCompleteTagInput = currentValue.substring(0, maxCuttingIndex);
  var newValue = existingCompleteTagInput + ' ' + currentResult.text + ', ';
  selectResult(null);
  clearResults();
  STATE.elems.input.val(newValue);
}

function handleKeydownInTagInput(e){
  /*
    if there is a currently selected result
    and someone hits "TAB KEY":
      add selected tag to the input value
  */
  var code = event.which;
  if( STATE.selectedResultIndex !== null ){
    if(code == TAB_KEY){
      addSelectedResult();
      e.preventDefault();
    }
  }
}

function handleKeyupInTagInput(e){
  /*
    if there are open results:
      up arrow selects the previous result
      down arrow selects the next result
    if the input key is a letter, dash, underscore or delete:
      update the autocomplete results
  */
  var code = event.which;
  if( STATE.results.length > 0 ){
    switch (code) {
      case UP_ARROW:
        selectPreviousResult();
        break;
      case DOWN_ARROW:
        selectNextResult();
        break;
    }
  }
  var key = String.fromCharCode(code);
  var tagSymbolMatch = key.match(/[A-Za-z\-_]/)
  if( tagSymbolMatch || code === DELETE_KEY ){
    updateAutocompleteSearchWithLatestValue();
  }
}

function handleResultClick(e){
  // adds the clicked item to the input value
  selectResult($(this).index())
  addSelectedResult();
}

function handleResultHover(e){
  // selects that result of the hovered item
  var index = $(this).index();
  if( index !== STATE.selectedResultIndex ){
    selectResult(index);
  }
}

function handleInputBlur(e){
  // clears and closes contents and state
  clearResults();
  resetState();
}

function handleInputFocus(e){
  // Sets the targeted widget and associated elements
  STATE.elems.input = $(e.target);
  STATE.elems.widget = STATE.elems.input.parents('.tags-cell');
  STATE.elems.resultsList = STATE.elems.widget.find(
    '.tags-autocomplete_results');
  console.log(STATE);
}


function handleAddTagsFormSubmission(e){
  e.preventDefault();
  var form = $(this);
  ajaxModule.handleForm(form, function (tags){
    var tagContainer = form.parents('.tags-input_module').find('.tags');
    var html = tags.map(templates.tag).join('');
    tagContainer.html(html);
    form.find("input[name='tags']").val('');
    clearResults();
  });
}

function removeHoverWarning(e){
  var targetedTag = $(e.target).parents('.tag');
  targetedTag.removeClass('danger');
}
function addHoverWarning(e){
  var targetedTag = $(e.target).parents('.tag');
  targetedTag.addClass('danger');
}

function handleTagRemovalClick(e){
  var targetedTag = $(e.target).parents('.tag');
  var tagId = targetedTag.attr("data-key");
  var appId = targetedTag.parents('.form_submission').attr("data-key");
  var actionUrl = '/tags/' + tagId + '/remove/' + appId + '/';
  $.post(actionUrl, {}, function (data){
    targetedTag.remove();
  })
}

function initTagWidgets(){
  tagSearch.init();
  resetState();
  var followups = $('.followups');
  followups.on('focusin', "input[name='tags']", handleInputFocus);
  followups.on('keydown', "input[name='tags']", handleKeydownInTagInput);
  followups.on('keyup', "input[name='tags']", handleKeyupInTagInput);
  followups.on('mousedown', ".autocomplete-result", handleResultClick);
  followups.on('mouseenter', ".autocomplete-result", handleResultHover);
  followups.on('blur', "input[name='tags']", handleInputBlur);
  followups.on('submit', 'form.tags-add_tags', handleAddTagsFormSubmission);
  followups.on('mouseenter', '.tag-remove', addHoverWarning);
  followups.on('mouseleave', '.tag-remove', removeHoverWarning);
  followups.on('click', '.tag-remove', handleTagRemovalClick);
}

module.exports = {
  init: initTagWidgets,
};