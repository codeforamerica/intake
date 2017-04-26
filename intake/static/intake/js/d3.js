var utils = require('./utils');
var d3 = require('d3-selection');
utils.combineObjs(d3, require('d3-array'));
utils.combineObjs(d3, require('d3-collection'));
utils.combineObjs(d3, require('d3-format'));
utils.combineObjs(d3, require('d3-axis'));
utils.combineObjs(d3, require('d3-scale'));
utils.combineObjs(d3, require('d3-shape'));
utils.combineObjs(d3, require('d3-time'));
utils.combineObjs(d3, require('d3-time-format'));

module.exports = d3;