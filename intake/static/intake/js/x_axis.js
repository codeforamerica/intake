var d3 = require('./d3');

var today = new Date();
var tomorrow = d3.timeDay.offset(today, 1);
tomorrow.setHours(0,0,0,0);
var niceDateFormat = d3.timeFormat("%b %e");

function getXTimeScale(sizes) {
	var startDate = d3.timeDay.offset(
		tomorrow,
		(sizes.xArrayLength * -1)
	);
	return d3.scaleTime()
		.domain([startDate, tomorrow])
		.range([0, sizes.chartWidth - sizes.xUnitWidth]);
}

function getXPositionScale(sizes) {
	var widthFactor = (sizes.chartWidth - sizes.xUnitWidth) / sizes.xArrayLength;
	return function(i){
		return i * widthFactor;
	}
}

function getXAxis (sizes) {
	// build the xAxis scale
	var timeScale = getXTimeScale(sizes);
	return d3.axisBottom(timeScale)
		.ticks(d3.utcMonday)
		.tickFormat(niceDateFormat);
}

module.exports = {
	timeScale: getXTimeScale,
	positionScale: getXPositionScale,
	axis: getXAxis,
}