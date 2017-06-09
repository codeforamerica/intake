// This is a manifest file that'll be compiled into application.js, which will include all the files
// listed below.
//
// Any JavaScript/Coffee file within this directory, lib/assets/javascripts, vendor/assets/javascripts,
// or any plugin's vendor/assets/javascripts directory can be referenced here using a relative path.
//
// It's not advisable to add code directly here, but if you do, it'll appear at the bottom of the
// compiled file.
//
// Read Sprockets README (https://github.com/rails/sprockets#sprockets-directives) for details
// about supported directives.
//
//= require jquery
//= require jquery_ujs
//= require_tree .


var incrementer = (function() {
  var i = {
    increment: function(input) {
      var max = parseInt($(input).attr('max'));
      var value = parseInt($(input).val());
      if(max != undefined) {
        if(value < max) {
          $(input).val(value+1);
        }
      }
      else {
        $(input).val(parseInt($(input).val())+1);
      }
    },
    decrement: function(input) {
      var min = parseInt($(input).attr('min'));
      var value = parseInt($(input).val());
      if(min != undefined) {
        if(value > min) {
          $(input).val(value-1);
        }
      }
      else {
        $(input).val(value-1);
      }

    },
    init: function() {
      $('.incrementer').each(function(index, incrementer) {
        var addButton = $(incrementer).find('.incrementer__add');
        var subtractButton = $(incrementer).find('.incrementer__subtract');
        var input = $(incrementer).find('.text-input');

        $(addButton).click(function(e) {
          i.increment(input);
        });

        $(subtractButton).click(function(e) {
          i.decrement(input);
        });
      });
    }
  }
  return {
    init: i.init
  }
})();

var radioSelector = (function() {
  var rs = {
    init: function() {
      $('.radio-button').each(function(index, button){
        if($(this).find('input').is(':checked')) {
          $(this).addClass('is-selected');
        }

        $(this).find('input').click(function(e) {
          $(this).parent().siblings().removeClass('is-selected');
          $(this).parent().addClass('is-selected');
        })
      })
    }
  }
  return {
    init: rs.init
  }
})();

var checkboxSelector = (function() {
  var cs = {
    init: function() {
      $('.checkbox').each(function(index, button){
        if($(this).find('input').is(':checked')) {
          $(this).addClass('is-selected');
        }

        $(this).find('input').click(function(e) {
          if($(this).is(':checked')) {
            $(this).parent().addClass('is-selected');
          }
          else {
            $(this).parent().removeClass('is-selected');
          }
        })
      })
    }
  }
  return {
    init: cs.init
  }
})();

var followUpQuestion = (function() {
  var fUQ = {
    init: function() {

      // if any initial questions are already selected on page load, show the follow up
      $('.question-with-follow-up__question').find('.radio-button, .checkbox').each(function(index, button) {
        if($(this).find('.question-with-follow-up__question input').is(':checked') && $(this).attr('data-follow-up') != null) {
          $($(this).attr('data-follow-up')).show();
        }
      });

      $('.question-with-follow-up').each(function(index, question) {
        var self = this;

        // if any initial questions are already selected on page load, show the follow up
        $(self).find('.question-with-follow-up__question').find('.radio-button, .checkbox').each(function(index, button) {
          if($(this).find('input').is(':checked') && $(this).attr('data-follow-up') != null) {
            $($(this).attr('data-follow-up')).show();
          }
        });

        // add click listeners to initial question inputs
        $(self).find('.question-with-follow-up__question input').click(function(e) {
          // reset follow ups
          $(self).find('.question-with-follow-up__follow-up input').attr('checked', false);
          $(self).find('.question-with-follow-up__follow-up').find('.radio-button, .checkbox').removeClass('is-selected');
          $(self).find('.question-with-follow-up__follow-up').hide();

          // show the current follow up
          $($(this).attr('data-follow-up')).show();
        })
      });
    }
  }
  return {
    init: fUQ.init
  }
})();

$(document).ready(function() {
  // incrementer.init();
  radioSelector.init();
  checkboxSelector.init();
  followUpQuestion.init();
});


