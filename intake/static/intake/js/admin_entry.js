window.$ = require('jquery');
window.jQuery = $;
var csrf = require('./csrf');
var utils = require('./utils');
var ajaxModule = require('./ajax');
var templates = require('./templates');
var tagWidget = require('./tag_widget');
var searchWidget = require('./application_search_widget');


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


function initializeEventListeners(){
	$('.notes_log').on('click', '.note-remove', handleNoteDeletionClick);
	$('form.note-create_form').on('submit', handleNewNoteFormSubmission);
	tagWidget.init();
	searchWidget.init();
}

function main(){
	var csrftoken = utils.getCookie('csrftoken');
	csrf.setupAjaxCsrf($, csrftoken);
	initializeEventListeners();
}

$(document).ready(main)