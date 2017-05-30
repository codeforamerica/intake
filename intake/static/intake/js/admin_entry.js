window.$ = require('jquery');
window.jQuery = $;
var csrf = require('./csrf');
var utils = require('./utils');
var ajaxModule = require('./ajax');
var templates = require('./templates');
var tagWidget = require('./tag_widget');
var searchWidget = require('./search_widget');


function handleNoteDeletionClick(e){
	// .target == delete note button
	// this == ./notes_log
	if( !confirm("Are you sure?") ){ return false; }
	var targetedNote = $(e.target).parents('.note');
	var noteId = targetedNote.attr("data-key");
	var actionUrl = '/notes/' + noteId + '/delete/';
	$.post(actionUrl, {}, function (data){ targetedNote.remove(); })
}

function handleNewNoteFormSubmission(e){
	// .target == Save note button
	// this == form
	e.preventDefault();
	var form = $(this);
	ajaxModule.handleForm(form, function (note){
		var html = templates.note(note);
		form.parents('.notes_log').find('.notes').prepend(html);
		form.find("[name='body']").val('');
	});
}

function renderApplicationSearchResults(results){
	$('ul.applications-autocomplete_results').html(
		results.map(templates.searchResult).join('')
	);
}

function renderEmptyApplicationSearchResults(){
	renderApplicationSearchResults([]);
}

var FOLLOWUP_SEARCH_RESULTS;
var FOLLOWUP_PAGE_CONTENTS;

function removeExistingFollowupResults(){
	if (FOLLOWUP_SEARCH_RESULTS){
		FOLLOWUP_SEARCH_RESULTS.remove();
	}
}
function renderFollowupSearchResults(htmlString){
	// find the followups list
	if (!FOLLOWUP_PAGE_CONTENTS){
		FOLLOWUP_PAGE_CONTENTS = $('tr.form_submission');
	}
	FOLLOWUP_PAGE_CONTENTS.hide();
	removeExistingFollowupResults();
	FOLLOWUP_SEARCH_RESULTS = $(htmlString);
	$('.followups').append(FOLLOWUP_SEARCH_RESULTS);
}

function renderEmptyFollowupSearchResults(){
	// remove previous search results
	removeExistingFollowupResults();
	if (FOLLOWUP_PAGE_CONTENTS){
		FOLLOWUP_PAGE_CONTENTS.show();
	}
}

function initializeEventListeners(){
	// these need to be high level to function properly
	$('.followups').on('click', '.note-remove', handleNoteDeletionClick);
	$('.followups').on(
		'submit', 'form.note-create_form', handleNewNoteFormSubmission);
	tagWidget.init();
	searchWidget(
		'.applications-search_module', '/applications-autocomplete/',
		renderApplicationSearchResults, renderEmptyApplicationSearchResults);
	searchWidget(
		'.followups-search_module', '/followups-autocomplete/',
		renderFollowupSearchResults, renderEmptyFollowupSearchResults);
}

function main(){
	var csrftoken = utils.getCookie('csrftoken');
	csrf.setupAjaxCsrf($, csrftoken);
	initializeEventListeners();
}

$(document).ready(main)