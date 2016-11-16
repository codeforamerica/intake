var config = require('./chart_configs');
var measures = require('./chart_size_measures');
var d3 = require('./d3');
var x = require('./x_axis');
var y = require('./y_axis');


var chartingFunctions = {
	bar: drawBarChart,
	line: drawLineChart,
	stream_fractions: drawStreamFractionsChart,
};


function drawBarChart (chart, chartConfig, sizes, data, xScale, yScale) {
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

function drawLineChart (chart, chartConfig, sizes, data, xScale, yScale) {
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

function drawStreamFractionsChart (chart, chartConfig, sizes, data, xScale, yScale) {

}

function getParentElementForOrg (orgData) {
	var classSelector = '.' + orgData.org.slug + ' .stats-chart_container_set';
	return  d3.select(classSelector);
}


function makeOrgChart (parent, chartConfig, orgData) {
	var dataArray = config.getDataForChart(chartConfig, orgData);
	if (dataArray === null) {
		// don't buld the chart if there is no data available.
		console.log(orgData.org.name, "no data for", chartConfig.chartName, "!!!");
		return;
	}
	console.log(orgData.org.name, "data for", chartConfig.chartName, "—");
	console.log(dataArray);
	var sizes = measures.sizes;
	// make container
	var container = parent.append("div").attr("class", "chart_container");
	// add title
	container.append('h4').text(chartConfig.chartName);
	var svg = container.append("svg")
		.attr("width", sizes.totalWidth)
		.attr("height", sizes.totalHeight);

	var yScale = y.scale(chartConfig.dataKey);
	y.axes(svg, chartConfig.dataKey);

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
	var chartFunction = chartingFunctions[chartConfig.chartType];
	chartFunction(chartGroup, chartConfig, sizes, dataArray, xScale, yScale);
	// add overlays & highlights if needed
}

function makeChartsForOrg (orgData) {
	// pull up org chart parent container
	var container = getParentElementForOrg(orgData);
	// draw each chart type for each org
	config.orgChartTypes.forEach(function(chartConfig){
		makeOrgChart(container, chartConfig, orgData);
	})
}

module.exports = {
	makeChartsForOrg: makeChartsForOrg
}