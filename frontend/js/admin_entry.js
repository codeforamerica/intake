var utils = require('./utils');

// get all the necessary d3 libraries
var d3 = require('d3-selection');
utils.combineObjs(d3, require('d3-collection'));
utils.combineObjs(d3, require('d3-axis'));
utils.combineObjs(d3, require('d3-scale'));
utils.combineObjs(d3, require('d3-time'));
utils.combineObjs(d3, require('d3-time-format'));


var applications = utils.getJson('applications_json');

var div = d3.select(".performance_chart");
div.append("h3").text("Daily Totals");

var days = d3.nest()
	.key(function(a){
		return applications.organizations[0].name;
	}).entries();

console.log(days);
/* we need:
	width
	height
	start date
	end date
	for each day:
		total finished applications
		total attempts at starting

*/
