var d3 = require('./d3');
var measures = require('./chart_size_measures');
var config = require('./chart_configs');


var maxYValues = {
	count: 12,
	weekly_total: 35,
	weekly_mean_completion_time: 60 * 60,
	weekly_median_completion_time: 16 * 60,
	weekly_dropoff_rate: 1.0,
};

var decimalFormat = d3.format(".1f");

var percentFormat = d3.format(".0%")

function niceDurationFormat(d){
	var minutes = Math.round(d / 60);
	return minutes + "m"
}

function noFormat(d){
	return d;
}

var yAxisTickFormats = {
	count: noFormat,
	weekly_total: noFormat,
	weekly_mean_completion_time: niceDurationFormat,
	weekly_median_completion_time: niceDurationFormat,
	weekly_dropoff_rate: percentFormat,
};

var yAxes = {};


function buildYScale(key) {
	var maxY = maxYValues[key];
	return d3.scaleLinear()
		.domain([0, maxY])
		.range([measures.sizes.chartHeight, 0]);
}


function calculateYMaxes(allData) {
	setWidth();
	var dataArray = config.getDataForChart(
		config.orgChartTypes[0], allData[0]);
	measures.setUnitWidth(dataArray);
	buildYAxes();
}

function setWidth(){
	var containers = d3.select('.stats-chart_container_set');
	measures.setTotalWidth(containers);
}

function buildYAxes(){
	var yTicks = 4;
	config.orgChartTypes.forEach(function(chartConfig, i){
		var key = chartConfig.dataKey;
		var yScale = buildYScale(key);
		var tickFormat = yAxisTickFormats[key];
		var yAxisLeft = d3.axisLeft(yScale)
			.ticks(yTicks)
			.tickFormat(tickFormat);
		var yAxisRight = d3.axisRight(yScale)
			.ticks(yTicks)
			.tickFormat(tickFormat);
		yAxes[key] = {
			left: yAxisLeft,
			right: yAxisRight,
		}
	});

};

function addYAxes(svg, key) {
	var sizes = measures.sizes;
	var leftAxis = yAxes[key].left;
	var rightAxis = yAxes[key].right;
	svg.append("g")
		.attr("class", "axis y right")
		.attr("transform", 
			measures.translate(
				sizes.offset.left + sizes.chartWidth,
				sizes.offset.top))
		.call(rightAxis);
	var fullWidthY = svg.append("g")
		.attr("class", "axis y left")
		.attr("transform",
			measures.translate(sizes.offset.left, sizes.offset.top)
		).call(leftAxis);
	// draw rules across the chart
	var lines = fullWidthY.selectAll("g.tick line");
	lines.attr("x1", sizes.chartWidth).attr("class", "back-ticks");
}

module.exports = {
	scale: buildYScale,
	axes: addYAxes,
	calculateMaxes: calculateYMaxes,
}