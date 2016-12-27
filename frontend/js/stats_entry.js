var utils = require('./utils');
var c3 = require('c3');
var moment = require('moment');


function buildChart1(data){
	var timeline = data.map(function (oneOrgsData) {
		var weeklyRates = oneOrgsData.weekly_totals.map(function(week) {
			week.date = moment(week.date).format('YYYY-MM-DD');
			week.count = Number(week.count);
			if (isNaN(week.count)) week.count = 0;
			return week;
			});
		return weeklyRates;
	});
	// this creates the xs reference x-axis that we will use
	var xs = {};
	var columns = [];
	data.forEach(function(org, i) {
		var name = org.org.name;
		var xName = 'x' + String(i + 1); 
		xs[name] = xName;
		// do somethigng that creates a column
		columns.push([xName].concat(timeline[i].map(function(d) {return d.date})));
		columns.push([name].concat(timeline[i].map(function(d) {return d.count})));
	});
	var chart1 = c3.generate({
		data: {
			xs: xs,
			columns: columns,
		},
		axis: {
			x: {
				type: 'timeseries',
			},
			y: {
				padding: {
					bottom:0
				}
			}
		},
		bindto: '#timeSeries'
	});
	return chart1;
}

function buildChart2(data) {
  var timeline = data.map(function (oneOrgsData) {
    var weeklyRates = oneOrgsData.weekly_totals.map(function(week) {
      week.date = moment(week.date).format('YYYY-MM-DD');
      week.count = Number(week.count);
      if (isNaN(week.count)) week.count = 0;
      return week;
    });
    return weeklyRates;
  });
  // this creates the xs reference x-axis that we will use
  var xs = {};
  var columns = [];
  data.forEach(function(org, i) {
    var name = org.org.name;
    var xName = 'x' + String(i + 1); 
    xs[name] = xName;
    // do somethigng that creates a column
    columns.push([xName].concat(timeline[i].map(function(d) {return d.date})));
    columns.push([name].concat(timeline[i].map(function(d) {return d.count})));
  });
  columns = columns.map(function(col) {
    if (col[0][0] !== 'x') {
      for (var i = 2; i < col.length; i++) {
        col[i] = col[i - 1] + col[i];
      }
    }
    return col;
  });
  var chart2 = c3.generate({
    data: {
      xs: xs,
      columns: columns,
    },
    axis: {
      x: {
        type: 'timeseries',
      },
      y: {
        padding: {
          bottom:0
        }
      }
    },
    bindto: '#timeSeriesGrowth'
  });
  return chart2;
}

function readDataAndDrawCharts(){
	// pull in JSON data
	var data = utils.getJson('applications_json');
  console.log("data", data);
	window.chart1 = buildChart1(data);
	window.chart2 = buildChart2(data);
}

readDataAndDrawCharts();