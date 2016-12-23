window.$ = require('jquery');
var csrf = require('./csrf');
var utils = require('./utils');

var templateRenderer = require('./templates');

function handleNoteDeletionClick(e){
	// .target == delete note button
	// this == ./notes_log
	if( !confirm("Are you sure?") ){ return false; }
	var targetedNote = $(e.target).parents('.note');
	var note_id = targetedNote.attr("id").replace('application_note-', '');
	var actionUrl = '/notes/' + note_id + '/delete/';
	$.post(actionUrl, {}, function (data){ targetedNote.remove(); })
}

function handleNewNoteFormSubmission(e){
	// .target == Save note button
	// this == form
	e.preventDefault();
	var form = $(this);
	var actionUrl = form.attr('action');
	var rawData = form.serializeArray();
	var data = {};
	rawData.forEach(function (field){ data[field.name] = field.value; });
	$.post(actionUrl, data, function (note){
		var html = templateRenderer.note(note);
		form.parents('.notes_log').find('.notes').prepend(html);
		form.find("[name='body']").val('');
	});
}

function initializeEventListeners(){
	$('.notes_log').on('click', '.note-remove', handleNoteDeletionClick);
	$('form.note-create_form').on('submit', handleNewNoteFormSubmission);
}

function main(){
	var csrftoken = utils.getCookie('csrftoken');
	csrf.setupAjaxCsrf($, csrftoken);
	initializeEventListeners();
}

$(document).ready(main)