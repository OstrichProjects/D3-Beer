var width = 330
    height = 495;

var y = d3.scale.linear()
    .range([0, height]);

var chart = d3.select(".chart")
    .attr("width", width)
    .attr("height", height + 45)
    .append("g")
    .attr("transform", "translate(0,45)")
    .attr("height", height);

var overlay = d3.select(".overlay")
    .attr("width", width)
    .attr("height", height + 45)
    .append("g")
    .attr("transform", "translate(0,45)")
    .attr("height", height);

var label = d3.select("#vis").append("div")
    .attr("class", "label")
    .style("opacity", 0);

if (document.getElementById("login")) {
    var url = "/login-beers";
} else {
    var url = "/beers";
}


d3.json(url)
    .on("error", function(e) { 
        alert("It took too long to get all of your checkins.  Try reloading in a minute or two."); 
    })
    .on("load", function(data) {

    if (data.hasOwnProperty('redirect')) {
        window.location = '/login';
    } else if (data.hasOwnProperty('error')) {
        alert("Your account ran out of API calls for the hour or Untappd's API is down.  Please try again in an hour.");
    }

    d3.select("#load").remove();

    d3.selectAll(".view").on('click', function(){
        d3.selectAll(".view").attr("class", "view");
        d3.select(this).attr("class", "view active");
        loadChart(this.value);
    });

    loadChart("style");

    function loadChart(type) {
        // Remove previous svg elements
        chart.selectAll("*").remove();
        overlay.selectAll("*").remove();
        
        // Creates an empty array with length = data
        total = 0;
        total = data.map(function(e) { total += 1 });
        
        var cutoff = 0;

        while (true) {
            // Creates Others object for selections with less than 2 entries
            others = {
                key: "Others",
                value: 0
            };

            // Maps the category entries into key name and length, adds to others if length < 2
            var checkins = d3.nest()
                .key(function(d) {return d[type]})
                .entries(data)
                .map(function(c) {
                    if (c.values.length > cutoff) {
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

            if (Object.keys(checkins).length > 19) {
                cutoff += 1
            } else { break; }
        }
        // Push others into Checkin object
        checkins.push(others);

        // Use more varied color scale if # categories is < 6
        if (Object.keys(checkins).length > 5) {
            var colourScale = d3.scale.category20b();
        } else {
            var colourScale = d3.scale.category10();
        }

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
            .attr("title", function(d) { return d.key; })
            .attr("fill", function(d,i) { return colourScale(i); });
        
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
    }
    })
    .get();