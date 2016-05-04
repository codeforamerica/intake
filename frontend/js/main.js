$( document ).ready(function() {
  addCSRFTokenToRequests()
  listenToEvents();
  getNewResponses();
});

var PDF_LOADING_STATES = [
  ["sending", 2000],
  ["generating", 13000],
  ["retrieving", 5000],
  ];

var TIMEOUT_HANDLES = {};

function addCSRFTokenToRequests(){
  // Taken directly from
  // http://flask-wtf.readthedocs.org/en/latest/csrf.html#ajax
  var csrftoken = $('meta[name=csrf-token]').attr('content');
  $.ajaxSetup({
      beforeSend: function(xhr, settings) {
          if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
              xhr.setRequestHeader("X-CSRFToken", csrftoken)
          }
      }
  });
}

function listenToEvents(){
  $('.responses-header').on('click', '.load_new_responses', getNewResponses);
  $('.container').on('click', '.pdf_button', getPDF);
}

function getNewResponses(e){
  $('button.load_new_responses').addClass('loading');
  $.ajax({
    url: API_ENDPOINTS.new_responses,
    success: handleNewResponses,
    error: handleLoadResponsesError,
    timeout: 10000
  });
}

function stateTransitionChain(target, stateStack, index){
  if( index > 0){
    var prevStateClassName = stateStack[index - 1][0];
    target.removeClass(prevStateClassName);
  }
  if( index == stateStack.length ){
    target.removeClass("loading");
    target.addClass('default');
    return;
  }
  var stateClassName = stateStack[index][0];
  var delay = stateStack[index][1];
  target.addClass(stateClassName);
  var handle = setTimeout(function(){
    stateTransitionChain(target, stateStack, index + 1);
  }, delay);
  TIMEOUT_HANDLES[target.attr('id')] = handle;
}

function getPDF(e){
  var target = $(this);
  target.removeClass("default");
  target.addClass('loading');
  var responseId = target.parents('.response').attr('id');
  responseId = responseId.split("-")[1]
  stateTransitionChain(target, PDF_LOADING_STATES, 0);
  $.ajax({
    method: "POST",
    url: target.attr("data-apiendpoint"),
    success: handleNewPDF(responseId),
    error: handleLoadPDFError(responseId),
    timeout: 20000
  });
}

function handleNewResponses(html){
  $('.responses').html(html);
  $('button.load_new_responses').removeClass('loading');
}

function handleNewPDF(responseId){
  return function(html){
    var button = $('#response-'+responseId).find('.pdf_button');
    var buttonId = button.attr('id');
    if( TIMEOUT_HANDLES[buttonId] ){
      var timeoutHandle = TIMEOUT_HANDLES[buttonId];
      clearTimeout(timeoutHandle);
    }
    button.replaceWith(html);
  };
}

function handleLoadResponsesError(jqXHR, error_type, error){
  var button = $('button.load_new_responses');
  button.removeClass('loading');
  button.addClass('error');
  button.html(
    '<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span> Problem connecting to Typeform'
  );
}

function handleLoadPDFError(responseId){
  return function(jqXHR, error_type, error){
    var response = $('#response-'+responseId);
    var button = response.find('.pdf_button')
    button.removeClass('loading');
    button.addClass('error');
    var buttonId = button.attr('id');
    if( TIMEOUT_HANDLES[buttonId] ){
      var timeoutHandle = TIMEOUT_HANDLES[buttonId];
      clearTimeout(timeoutHandle);
    }
  };
}