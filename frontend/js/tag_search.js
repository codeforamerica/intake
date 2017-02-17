var utils = require('./utils');

var searchModule = {};

function buildSearchFunction(searchSpace){
  return function (searchTerm){
    searchTerm = searchTerm.trim();
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
    // previlege matches in the beginning of the word
    results.sort(function(a, b){
      return a.prefix.length - b.prefix.length;
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