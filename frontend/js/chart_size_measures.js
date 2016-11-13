var offset = {left: 20, right: 20, bottom: 40, top: 20};
var totalHeight = 140;

function getSizes(container, dataArray) {
	var totalWidth = container.property("offsetWidth");
	var chartWidth = totalWidth - (offset.left + offset.right);
	var xArrayLength = dataArray.length;
	var xUnitWidth = chartWidth / xArrayLength;
	return {
		offset: offset,
		totalHeight: totalHeight,
		totalWidth: totalWidth,
		chartWidth: chartWidth,
		chartHeight: totalHeight - (offset.bottom + offset.top),
		xArrayLength: xArrayLength,
		xUnitWidth: xUnitWidth,
		barShift: xUnitWidth * 0.6,
	};
}

function translate(x, y){
	return "translate(" + x + "," + y + ")";
}

module.exports = {
	getSizes: getSizes,
	translate: translate,
};