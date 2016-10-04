var utils = require('./utils');

// get all the necessary d3 libraries
var d3 = require('d3-selection');
utils.combineObjs(d3, require('d3-array'));
utils.combineObjs(d3, require('d3-collection'));
utils.combineObjs(d3, require('d3-axis'));
utils.combineObjs(d3, require('d3-scale'));
utils.combineObjs(d3, require('d3-time'));
utils.combineObjs(d3, require('d3-time-format'));



function drawDailyCountsChart(){
	var totalHeight = 170;
	var offset = {left: 20, right: 20, bottom: 40, top: 20};
	var yearMonthDayFormat = d3.timeFormat("%Y-%m-%d");
	var niceDateFormat = d3.timeFormat("%a %b %e");

	var applications = utils.getJson('applications_json');
	var div = d3.select(".performance_chart");
	div.append("h3").text("Daily Totals");
	var totalWidth = div.property("offsetWidth");
	var chartWidth = totalWidth - (offset.left + offset.right);
	var chartHeight = totalHeight - (offset.bottom + offset.top);

	var today = new Date();
	today.setHours(0,0,0,0);
	var startDate = d3.timeMonth.offset(today, -2);
	var allDays = d3.timeDays(startDate, today);
	var barWidth = chartWidth / allDays.length;

	var dayBuckets = d3.nest()
		.key(function(a){ return yearMonthDayFormat(new Date(a.started)); })
		.rollup(function(applications){
			var finished = applications.filter(function(a){ return a.finished; });
			return {
				finished: finished.length,
				total: applications.length,
				unfinished: applications.length - finished.length,
				applications: applications,
			};
		}).map(applications, d3.map);

	var xScale = d3.scaleTime()
		.domain([startDate, today])
		.range([0, chartWidth - barWidth]);

	var yScale = d3.scaleLinear()
		.domain([0, d3.max(dayBuckets.values(), function(d){ return d.finished; })])
		.range([chartHeight, 0]);

	var svg = div.append("svg")
		.attr("width", totalWidth)
		.attr("height", totalHeight);

	var yAxisLeft = d3.axisLeft(yScale)
		.ticks(5);
	var yAxisRight = d3.axisRight(yScale)
		.ticks(5);
	svg.append("g")
		.attr("class", "axis y right")
		.attr("transform", "translate("+(offset.left+chartWidth)+","+offset.top+")")
		.call(yAxisRight);
	var leftAxis = svg.append("g")
		.attr("class", "axis y left")
		.attr("transform", "translate("+offset.left+","+offset.top+")")
		.call(yAxisLeft);
	var lines = leftAxis.selectAll("g.tick line");
	lines.attr("x1", chartWidth).attr("class", "back-ticks");

	var xAxis = d3.axisBottom(xScale)
		.ticks(d3.timeWeek);

	svg.append("g")
		.attr("class", "axis x")
		.attr("transform", "translate("+offset.left+","+(chartHeight+offset.top)+")")
		.call(xAxis);

	var chart = svg.append("g")
		.attr("transform", "translate("+offset.left+","+offset.top+")");
	var dayBars = chart.selectAll("rect")
		.data(allDays)
		.enter()
		.append("rect")
		.attr("class", "day_bar")
		.attr("height", function(d){
			var counts = dayBuckets.get(yearMonthDayFormat(d));
			var count = counts ? counts.finished : 0;
			return chartHeight - yScale(count);
		}).attr("y", function (d){
			var height = this.getAttribute("height");
			return chartHeight - height;
		}).attr("width", barWidth)
		.attr("x", xScale);



}



drawDailyCountsChart();
/* we need:
	width
	height
	start date
	end date
	for each day:
		total finished applications
		total attempts at starting

*/
