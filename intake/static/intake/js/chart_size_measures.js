var offset = {left: 30, right: 30, bottom: 40, top: 20};
var totalHeight = 140;
var totalWidth = 555;
var chartWidth = totalWidth - (offset.left + offset.right);
var xArrayLength = 62;
var xUnitWidth = chartWidth / xArrayLength;
var sizes;


function updateSizes() {
	chartWidth = totalWidth - (offset.left + offset.right);
	xUnitWidth = chartWidth / xArrayLength;
	sizes = {
			offset: offset,
			totalHeight: totalHeight,
			totalWidth: totalWidth,
			chartWidth: chartWidth,
			chartHeight: totalHeight - (offset.bottom + offset.top),
			xArrayLength: xArrayLength,
			xUnitWidth: xUnitWidth,
			barShift: xUnitWidth * 0.6,
	};
	return sizes;
}


function setTotalWidth(container) {
	totalWidth = container.property("offsetWidth");
	return updateSizes();
}


function setUnitWidth(dataArray) {
	xArrayLength = dataArray.length;
	return updateSizes();
}


function getSizes(container, dataArray) {
	setTotalWidth(container);
	return setUnitWidth(dataArray);
}


function translate(x, y){
	return "translate(" + x + "," + y + ")";
}


updateSizes();
module.exports = {
	getSizes: getSizes,
	translate: translate,
	setTotalWidth: setTotalWidth,
	setUnitWidth: setUnitWidth,
	sizes: sizes,
};