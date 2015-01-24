var colourScale = d3.scale.category20b();

var width = 330
    height = 540;

var y = d3.scale.linear()
    .range([0, height]);

var chart = d3.select(".chart")
    .attr("width", width)
    .attr("height", height)
    .append("g")
    .attr("transform", "translate(0,45)");

var overlay = d3.select(".overlay")
    .attr("width", width)
    .attr("height", height)
    .append("g")
    .attr("transform", "translate(0,45)");

var label = d3.select("#vis").append("div")
    .attr("class", "label")
    .style("opacity", 0);

var url = "/test-beers"

function loadChart(type) {
    d3.json(url, function(error, data) {
        // Remove previous svg elements
        chart.selectAll("*").remove();
        overlay.selectAll("*").remove();
        
        // Creates an empty array with length = data
        total = 0;
        total = data.map(function(e) { total += 1 });
        
        // Creates Others object for selections with less than 2 entries
        others = {
            key: "Others",
            value: 0
        };
    
        // Maps the category entries into key name and length, adds to others if length < 2
        checkins = d3.nest()
            .key(function(d) {return d[type]})
            .entries(data)
            .map(function(c) {
                if (c.values.length > 1) {
                    return {
                        key: c.key,
                        value: c.values.length
                    }
                } else {
                    others.value += c.values.length
                    return null
                }
            })
            .filter(function(c) { return c != null })
            .sort(function(a,b) { return b.value - a.value });

        // Push others into Checkin object
        checkins.push(others);

        y.domain([0, data.length]);
        var y0 = 0;

        checkins = checkins.map(function(c) {
            return {
                key: c.key,
                value: c.value,
                y0: y0,
                y1: y0 += y(c.value) // increments y0 for next value
            }
        });

        chart.selectAll(".bar")
            .data(checkins)
            .enter().append("rect")
            .attr("class", "bar")
            .attr("x", 0)
            .attr("y", function(d) { return d.y0; })
            .attr("height", function(d) { return y(d.value); })
            .attr("width", width)
            .attr("title", function(d) { return d.key })
            .attr("fill", function(d,i) { return colourScale(i) });
        
        overlay.selectAll(".bar")
            .data(checkins)
            .enter().append("rect")
            .attr("class", "bar")
            .attr("x", 0)
            .attr("y", function(d) { return d.y0 })
            .attr("height", function(d) { return y(d.value); })
            .attr("width", width)
            .attr("title", function(d) { return d.key })
            .style("opacity", 0)
            .on('mouseover', function(d) {
                label.transition()
                    .duration(200)
                    .style("opacity", .9);
                
                label.html("<strong>" + d.key + "</strong>: " + d.value )
                    .style("top", ((d.y1 - d.y0) / 2 + d.y0) + 26 + "px")
            })
            .on('mouseout', function(d) {
                label.transition()
                    .duration(200)
                    .style("opacity", 0);
            });

        chart.append("rect")
            .attr("width", 330)
            .attr("height", height)
            .attr("fill", "#FDF8F2")
            .attr("transform", "translate(0,0)")
            .transition()
            .duration(2000)
            .attr("height", 0)
    });
}

(function() {
  loadChart('style');
  d3.selectAll(".view").on('click', function(){
    loadChart(this.value)
  });
})();