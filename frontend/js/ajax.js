var $ = require('jquery');

function handleAjaxFormSubmission(form, successCallback){
  var actionUrl = form.attr('action');
  var rawData = form.serializeArray();
  var data = {};
  rawData.forEach(function (field){ data[field.name] = field.value; });
  console.log(actionUrl, "POST:", data);
  // $.post(actionUrl, data, successCallback);
  var tags = data['tags'].trim().split(/[, ]+/).map(
    function (d, i){ return {slug: d, id: i}; })
  successCallback(tags);
}

module.exports = {
  handleForm: handleAjaxFormSubmission,
}