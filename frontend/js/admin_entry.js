var utils = require('./utils');
var org_charts = require('./org_charts');
var y = require('./y_axis');

// get all the necessary d3 libraries
var d3 = require('./d3');


function readDataAndDrawCharts(){
	// pull in JSON data
	var all_applications_data = utils.getJson('applications_json');
	y.calculateMaxes(all_applications_data);
	all_applications_data.forEach(org_charts.makeChartsForOrg);
	// Loop through orgs, for each org
}



readDataAndDrawCharts();