var utils = require('./utils');

var exampleSearchSpace = [
  'apple', 'banana', 'cherry', 'durian', 'eggplant',
  'fig', 'guava', 'honeydew', 'kiwi', 'lemon', 'melon', 'nectarine',
  'orange', 'peach', 'quince', 'raspberry', 'strawberry'
];

var searchModule = {};

function buildSearchFunction(searchSpace){
  return function (searchTerm){
    var termLength = searchTerm.length;
    var results = [];
    if( termLength < 1 ){
      return results;
    }
    searchSpace.forEach(function(possibleResult){
      var match = possibleResult.match(searchTerm);
      if( match ){
        var prefix = possibleResult.substring(0, match.index);
        var suffix = possibleResult.substring(match.index + termLength);
        results.push({
          text: possibleResult,
          prefix: prefix,
          suffix: suffix,
          selection: searchTerm,
        });
      }
    });
    return results;
  }
}

searchModule.init = function (){
  var tagData = utils.getJson('applications_json');
  if (!tagData) { tagData = exampleSearchSpace; }
  searchModule.searchTags = buildSearchFunction(tagData);
};

module.exports = searchModule;