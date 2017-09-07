//======================================================================

var svg = document.documentElement; // Top level element

//======================================================================

class Transform1D {
  constructor(scale, offset) {
    this.scale = scale;
    this.offset = offset;
  }
  transform(x) {
    return x*this.scale + this.offset;
  }
  inverse(x) {
    return (x - this.offset)/this.scale;
  }
}

//======================================================================

class Trace {
  constructor(id, time_transform=null, value_transform=null, visualiser=null) {
    this.line = svg.getElementById(id).getElementsByTagName("path")[0]
    if (this.line) {
      this.points = new Float64Array(JSON.parse('[' + this.line.getAttribute('d').split(/M|L| /).filter(i => i != '').join(',') + ']'));
      this.marker = document.createElementNS(svg.namespaceURI, 'circle');
      this.marker.setAttribute("r","3");
      this.marker.style.stroke = "none";
      this.marker.style.fill = this.line.style["stroke"]
      svg.appendChild(this.marker);
      if (time_transform) this.time_transform = time_transform;
      else                this.time_transform = new Transform1D(1.0, 0.0);
      if (value_transform) this.value_transform = value_transform;
      else                 this.value_transform = new Transform1D(1.0, 0.0);
      this.visualiser = visualiser;
    }
  }

  draw(from, to) {
    var mx, my;
    var path = "";
    var xy = this.points;
    var start = this.time_transform.transform(from);
    var t = this.time_transform.transform(to);

    // Find first point just before `time`

    var i = 0;
    while (i < xy.length && xy[i] < start)
      i += 2;
    // Now have start <= xy[i]

    if (i < xy.length) {
      if (i > 0 && start < xy[i]) {
        var dt = start - xy[i-2];
        var dy = dt*(xy[i+1]-xy[i-1])/(xy[i]-xy[i-2]);
        mx = start; my = xy[i-1] + dy;
      } else {
        mx = xy[i];
        my = xy[i+1];
      }
      path = "M " + String(mx) + " " + String(my);
      if (t > xy[i]) {
        i += 2;
        while (i < xy.length && xy[i] <= t) {
          mx = xy[i]; my = xy[i+1];
          if (i == 2) path += " L";
          path += " " + String(mx) + " " + String(my);
          i += 2;
        }
        if (i < xy.length) {  // xy[i-2] <= t < xy[i]
          var dt = t - xy[i-2];
          var dy = dt*(xy[i+1]-xy[i-1])/(xy[i]-xy[i-2]);
          mx = t; my = xy[i-1] + dy;
          path += " l" + String(dt) + " " + String(dy);
        }
      }
      if (this.visualiser)
        this.visualiser(to, this.value_transform.inverse(my));
    }
    if (path == "") {
      this.marker.setAttribute("visibility", "hidden");
    } else {
      this.line.setAttribute("d", path);
      this.marker.setAttribute("cx", mx);
      this.marker.setAttribute("cy", my);
      this.marker.setAttribute("visibility", "visible");
    }
  }
};

//======================================================================

class Animation {
  constructor(start, end, step) {
    this.start_time = start;
    this.end_time = end;
    this.time_step = step;
    this.traces = [];
    this.time = this.start_time;
    this.animation = null;
  }
  add_trace(trace) {
    this.traces.push(trace);
  }
  draw_traces(time) {
    for (let trace of this.traces)
      trace.draw(this.start_time, time);
  }
  animate() {
    this.draw_traces(this.time);
    this.time += this.time_step;
    if (this.time > this.end_time)
      this.time = this.start_time;
  }
  start(period) {
    if (this.animation == null)
      this.animation = setInterval(this.animate.bind(this), period);
  }
  stop() {
    if (this.animation != null) {
      clearInterval(this.animation);
      this.animation = null;
    }
  }
};

//======================================================================
