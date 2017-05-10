var $ = require('jquery');

function handleAjaxFormSubmission(form, successCallback){
  var actionUrl = form.attr('action');
  var rawData = form.serializeArray();
  var data = {};
  rawData.forEach(function (field){ data[field.name] = field.value; });
  $.post(actionUrl, data, successCallback);
}

module.exports = {
  handleForm: handleAjaxFormSubmission,
}