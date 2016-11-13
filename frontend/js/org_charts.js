var config = require('./chart_configs');
var measures = require('./chart_size_measures');
var d3 = require('./d3');
var x = require('./x_axis');
var maxYValues = {};


var chartingFunctions = {
	bar: drawBarChart,
	line: drawLineChart,
	stream_fractions: drawStreamFractionsChart,
};


function drawBarChart (chart, config, sizes, data, xScale, yScale) {
	chart.selectAll("rect")
		.data(data).enter()
		.append("rect")
		.attr("class", "day-bar")
		.attr("height", function(d){
			var value = d ? d : 0;
			return sizes.chartHeight - yScale(value);
		}).attr("y", function(d){
			return sizes.chartHeight - this.getAttribute("height");
		}).attr("width", sizes.xUnitWidth - 1)
		.attr("x", function(d, i){
			return xScale(i) + sizes.barShift;
		});
}

function drawLineChart (chart, config, sizes, data, xScale, yScale) {
	var line = d3.line()
		.x(function (d, i){
			return xScale(i);
		}).y(function (d){
			return yScale(d);
		});
	chart.append("path")
		.datum(data)
		.attr("class", "day-line")
		.attr("d", line);
}

function drawStreamFractionsChart (chart, config, sizes, data, xScale, yScale) {

}

function getParentElementForOrg (orgData) {
	var classSelector = '.' + orgData.org.slug + ' .stats-chart_container_set';
	return  d3.select(classSelector);
}


function getDataForChart(config, orgData) {
	// take the 'days' or 'apps' attribute and pull out an array
	// based on the config key
	if (orgData.days[0][config.dataKey] === undefined) {
		return null;
	}
	return orgData.days.map(function(dayDatum){
		return dayDatum[config.dataKey];
	});
}

function getMaxY(key, data){
	if (!maxYValues.hasOwnProperty(key)) {
		maxYValues[key] = d3.max(data);
	}
	return maxYValues[key];
}

function buildYScale(sizes, config, data) {
	var maxY = getMaxY(config.dataKey, data);
	return d3.scaleLinear()
		.domain([0, maxY])
		.range([sizes.chartHeight, 0]);
}

function addYAxes(svg, sizes, yScale) {	
	var yTicks = 4;
	var yAxisLeft = d3.axisLeft(yScale)
		.ticks(yTicks );
	var yAxisRight = d3.axisRight(yScale)
		.ticks(yTicks);
	svg.append("g")
		.attr("class", "axis y right")
		.attr("transform", 
			measures.translate(
				sizes.offset.left + sizes.chartWidth,
				sizes.offset.top))
		.call(yAxisRight);
	var leftAxis = svg.append("g")
		.attr("class", "axis y left")
		.attr("transform",
			measures.translate(sizes.offset.left, sizes.offset.top)
		).call(yAxisLeft);
	// draw rules across the chart
	var lines = leftAxis.selectAll("g.tick line");
	lines.attr("x1", sizes.chartWidth).attr("class", "back-ticks");
}

function makeOrgChart (parent, config, orgData) {
	var dataArray = getDataForChart(config, orgData);
	if (dataArray === null) {
		// don't buld the chart if there is no data available.
		console.log(orgData.org.name, "no data for", config.chartName, "!!!");
		return;
	}
	console.log(orgData.org.name, "data for", config.chartName, "—");
	console.log(dataArray);
	var sizes = measures.getSizes(parent, dataArray);
	console.log("sizes", sizes);
	// make container
	var container = parent.append("div").attr("class", "chart_container");
	// add title
	container.append('h4').text(config.chartName);
	var svg = container.append("svg")
		.attr("width", sizes.totalWidth)
		.attr("height", sizes.totalHeight);

	// build y scale
	var yScale = buildYScale(sizes, config, dataArray);
	addYAxes(svg, sizes, yScale);

	// add axes
	var xScale = x.positionScale(sizes);
	var xAxis = x.axis(sizes);
	svg.append("g")
		.attr("class", "axis x")
		.attr("transform", 
				measures.translate(
					sizes.offset.left,
					sizes.chartHeight + sizes.offset.top
					))
		.call(xAxis);
	var chartGroup = svg.append("g")
		.attr("transform", measures.translate(
			sizes.offset.left, sizes.offset.top));
	// add geometry
	var chartFunction = chartingFunctions[config.chartType];
	chartFunction(chartGroup, config, sizes, dataArray, xScale, yScale);
	// add overlays & highlights if needed
}

function makeChartsForOrg (orgData) {
	// pull up org chart parent container
	var container = getParentElementForOrg(orgData);
	// draw each chart type for each org
	config.orgChartTypes.forEach(function(config){
		makeOrgChart(container, config, orgData);
	})
}

module.exports = {
	makeChartsForOrg: makeChartsForOrg
}