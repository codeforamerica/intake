var chartTypeConfigs = [
	{
		dataKey: "count",
		chartType: "bar",
		chartName: "Daily Totals",
	},
	{
		dataKey: "weekly_total",
		chartType: "line",
		chartName: "Weekly Rate",
	},
	{
		dataKey: "weekly_mean_completion_time",
		chartType: "line",
		chartName: "Mean Completion Time (7-day rolling)",
	},
	{
		dataKey: "weekly_median_completion_time",
		chartType: "line",
		chartName: "Median Completion Time (7-day rolling)",
	},
	{
		dataKey: "referrers",
		chartType: "stream_fractions",
		chartName: "Referring domains (7-day rolling)",
	},
	{
		dataKey: "weekly_dropoff_rate",
		chartType: "line",
		chartName: "Percent drop off (7-day rolling)",
	}
];

function getDataForChart(chartConfig, orgData) {
	// take the 'days' or 'apps' attribute and pull out an array
	// based on the chartConfig key
	if (orgData.days[0][chartConfig.dataKey] === undefined) {
		return null;
	}
	return orgData.days.map(function(dayDatum){
		return dayDatum[chartConfig.dataKey];
	});
}

module.exports = {
	orgChartTypes: chartTypeConfigs,
	getDataForChart: getDataForChart,
}