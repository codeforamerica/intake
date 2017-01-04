var utils = require('./utils');

var searchModule = {};

function buildSearchFunction(searchSpace){
  return function (searchTerm){
    var termLength = searchTerm.length;
    var results = [];
    if( termLength < 1 ){
      return results;
    }
    searchSpace.forEach(function(possibleResult){
      var match = possibleResult.toLowerCase().match(
        searchTerm.toLowerCase());
      if( match ){
        var prefix = possibleResult.substring(0, match.index);
        var selection = possibleResult.substring(
          match.index, match.index + termLength);
        var suffix = possibleResult.substring(match.index + termLength);
        results.push({
          text: possibleResult,
          prefix: prefix,
          suffix: suffix,
          selection: selection,
        });
      }
    });
    return results;
  }
}

searchModule.init = function (){
  var tagData = utils.getJson('tags_json');
  if (!tagData) { tagData = []; }
  searchModule.searchTags = buildSearchFunction(tagData);
};

module.exports = searchModule;