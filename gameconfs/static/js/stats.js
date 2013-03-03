/* Generate country stat table */

var x_extent = d3.extent(country_data, function(d){ return d[1] });
var x_scale = d3.scale.linear()
    .range([0, 200])
    .domain([0, x_extent[1]]);

var table_rows = d3.select("table#country-stats")
    .selectAll("tr")
    .data(country_data)
    .enter()
    .append("tr");

table_rows.append("td")
    .text(function(d){ return d[0]; });

bar_cell = table_rows.append("td");

bar_cell.append("span")
    .attr("class", "bar")
    .style("width", function(d){ return x_scale(d[1]) + "px";})
    .text(".");

bar_cell.append("span")
    .attr("class", "bar_label")
    .text(function(d){ return d[1];});

/* Generate city stat table */

x_extent = d3.extent(city_data, function(d){ return d[1] });
x_scale = d3.scale.linear()
    .range([0, 200])
    .domain([0, x_extent[1]]);

table_rows = d3.select("table#city-stats")
    .selectAll("tr")
    .data(city_data)
    .enter()
    .append("tr");

table_rows.append("td")
    .text(function(d){ return d[0]; });

bar_cell = table_rows.append("td");

bar_cell.append("span")
    .attr("class", "bar")
    .style("width", function(d){ return x_scale(d[1]) + "px";})
    .text(".");

bar_cell.append("span")
    .attr("class", "bar_label")
    .text(function(d){ return d[1];});
