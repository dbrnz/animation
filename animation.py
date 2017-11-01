import io
from lxml import etree as ET

import matplotlib
matplotlib.use('svg')  ## Otherwise transforms are wrong with tight-layout...

from matplotlib import pyplot as plt
from matplotlib.transforms import Affine2D



POINTS_PER_INCH = 72.0

# Embedded Javascript

ANIMATION_SCRIPT = '''
    // Top level element
    var svg = document.documentElement;

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

    class Trace {
      constructor(id, time_transform=null, value_transform=null, visualiser=null) {
        var path_id = id + "_path";
        this.path = svg.getElementById(path_id);
        if (this.path)
          this.points = new Float64Array(JSON.parse("[" + this.path.getAttribute("d").split(/M|L| /).filter(i => i != "").join(",") + "]"));
        var trace = svg.getElementById(id);
        this.line = trace ? trace.getElementsByTagName("path")[0] : null;
        if (this.line) {
          this.marker = document.createElementNS(svg.namespaceURI, "circle");
          this.marker.setAttribute("r","3");
          this.marker.style.stroke = "none";
          this.marker.style.fill = this.line.style["stroke"]
          svg.appendChild(this.marker);
        }
        if (time_transform) this.time_transform = time_transform;
        else                this.time_transform = new Transform1D(1.0, 0.0);
        if (value_transform) this.value_transform = value_transform;
        else                 this.value_transform = new Transform1D(1.0, 0.0);
        this.visualiser = visualiser;
      }

      draw(from, to) {
        var mx, my;
        var path = "";
        var xy = this.points;
        var start = this.time_transform.transform(from);
        var t = this.time_transform.transform(to);

        // Find first point just before `time`
        var i = 0;
        while (i < xy.length && xy[i] < start) {
          i += 2;
        }

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
        } else if (this.line) {
          this.line.setAttribute("d", path);
          this.marker.setAttribute("cx", mx);
          this.marker.setAttribute("cy", my);
          this.marker.setAttribute("visibility", "visible");
        }
      }
    };

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
'''


class Visualiser(object):
    def __init__(self, id, position, setup_js, call_js):
        self._id = id
        self._position = position   # (x, y) on Axes scale??
        self._setup_js = setup_js
        self._call_js = call_js

    def get_pos(self, plot):
        return plot.get_figure().make_flip_transform(plot.transAxes).transform(self._position)

    def setup_js(self):
        return self._setup_js

    def call_js(self):
        return self._call_js

    def svg(self, plot):
        pass


class CircleVisualiser(Visualiser):
    def __init__(self, id, position, fill, *args):
        super().__init__(id, position, *args)
        self._fill = fill

    def svg(self, plot):
        pos = self.get_pos(plot)
        return ET.Element('circle',
                          dict(id=self._id, cx='%g' % pos[0], cy='%g' % pos[1], r='0', fill=self._fill))


class Animation(object):
    def __init__(self, id, trace, display, marker, visualiser):
        trace.set_gid(id)
        self.id = id
        self.trace = trace
        self.display = display
        self.marker = marker
        self.visualiser = visualiser


class Figure(matplotlib.figure.Figure):
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self._animations = []
        self._next_id = 0
        self._script = []
        self._xml = []

    def close(self):
        plt.close(self)

    def add_animation(self, trace, id=None, display='animate', marker=True, timing=None, visualiser=None):
        if display in [None, 'hidden', 'visible'] and not marker and visualiser is None:
            raise ValueError('Nothing to animate...')
        if id is None:
            id = 'trace_%s' % self._next_id
            self._next_id += 1
        self._animations.append(Animation(id, trace, display, marker, visualiser))
        return id

    def add_script(self, script):
        self._script.append(script)

    def add_xml(self, xml):  ## Also allow a list and extend??
        self._xml.append(xml)

    # Based on _make_flip_transform() in matplotlib/backend_svg.py
    def make_flip_transform(self, transform):
        return (transform +
                Affine2D()
                .scale(POINTS_PER_INCH/self.dpi)
                .scale(1.0, -1.0)
                .translate(0.0, POINTS_PER_INCH*self.get_figheight()))


    def generate_svg(self, start, end, step, units='ms', speed=1.0, period=10, **kwds):  ## Period in ms
        if units not in ['ms', 's', 'm', 'h', 'd']:
            raise ValueError('Unknown timing units')

        ## Allow for units and scale everything?? Adjust speed ???

        step *= speed

        self.add_script('var animation = new Animation(%g, %g, %g);' % (start, end, step))

        # Save figure as SVG to an in-memory file and before using transforms
        # since backend can adjust them

        svg = io.BytesIO()
        super().savefig(svg, format='svg') #, bbox_inches='tight') #, pad_inches=0, **kwds)  ## dpi=1000,

        # Get the XML tree for the SVG

        svg_tree = ET.XML(svg.getvalue())

        # Generate SVG to animate our traces and visualisers

        for animation in self._animations:
            trace = animation.trace
            plot = trace.axes

            path = svg_tree.find('.//svg:g/svg:g/svg:g[@id="{id}"]/svg:path'.format(id=animation.id),
                                 {'svg': 'http://www.w3.org/2000/svg'})
            d = path.get('d')
            self.add_xml(ET.XML('<defs><path id="{id}_path" d="{d}"/></defs>'.format(id=animation.id, d=d)))
            # Affine matrix to transform world coordinates into SVG point-based coordinates
            xfm = self.make_flip_transform(plot.transData).get_matrix()
            if animation.visualiser:
                self.add_xml(animation.visualiser.svg(plot))
                self.add_script(animation.visualiser.setup_js())
                invoke_visualiser = ', %s' % animation.visualiser.call_js()
            else:
                invoke_visualiser = ''

            self.add_script('animation.add_trace(new Trace("%s", new Transform1D(%f, %f), new Transform1D(%f, %f) %s));'
                                                % (animation.id,    xfm[0, 0], xfm[0, 2],    xfm[1, 1], xfm[1, 2],
                                                                                                        invoke_visualiser))
        self.add_script('animation.start(%g);' % period)

        script_element = ET.Element('script', {'type': 'application/ecmascript'})
        script_element.text = '<![CDATA[%s]]>' % '\n'.join(self._script)
        self.add_xml(script_element)

        # Insert animation SVG into the XML tree

        svg_tree.extend(self._xml)

        # Return SVG as a Unicode string. A method of 'html' ensures
        # that '<', '>' and '&' are not escaped.

        return ET.tostring(svg_tree, encoding='unicode', method='html')


def figure(**kwds):
    return plt.figure(FigureClass=Figure, tight_layout=True, **kwds)









'''

if __name__ == '__main__':

    import OpenCOR as oc

    t  = [0, 1, 2, 3, 4, 5, 6, 7, 7, 9]
    v  = [0, 1, 2, 3, 4, 4, 3, 2, 1, 0]
    na = [9, 8, 7, 6, 5, 4, 5, 6, 7, 8]


    fig = figure()

    fig.add_script(ANIMATION_SCRIPT)

## Define standard gradients...
    fig.add_xml(ET.XML('''<defs>
      <radialGradient id="RedGradient">
          <stop offset="10%" stop-color="red" />
          <stop offset="100%" stop-color="white" />
      </radialGradient>
    </defs>'''))

    sodium_visualiser = CircleVisualiser('sodium', (0.9, 0.8),
                                          'url(#RedGradient)',
                                          'var sodiumVar = svg.getElementById("sodium");',
                                          '(t, y) => { sodiumVar.setAttribute("r", 5*(y-2)); }')
    sodium_plot = fig.add_subplot(211, xlabel='Time (ms)', ylabel='Na i (millimolar)')
    sodium_trace = sodium_plot.plot(t, na, lw=1)[0]
    fig.add_animation(sodium_trace, visualiser=sodium_visualiser)

    voltage_visualiser = CircleVisualiser('voltage', (0.9, 0.8),
                                          'url(#RedGradient)',
                                          'var voltageVar = svg.getElementById("voltage");',
                                          '(t, y) => { voltageVar.setAttribute("r", 5*(y+1)); }')
    voltage_plot = fig.add_subplot(212, xlabel='Time (ms)', ylabel='Membrane voltage (mV)')
    voltage_trace = voltage_plot.plot(t, v, lw=1)[0]   ## Set colour...
    fig.add_animation(voltage_trace, visualiser=voltage_visualiser)

## Auto determine max T and speed
    svg = fig.generate_svg(0, 10, 1, speed=0.1)
    fig.close()

    browser = oc.browserWebView()
    browser.setContent(svg, "image/svg+xml")

'''

## Options to show marker, animate trace

## Option to only visualise (==> no plot/subplot, need to pass (t, y) arrays)

1) Animated trace with marker, with or without visualiser          A A x 2
                                                                   A N x 2
2) No trace but animated marker, with or without visualiser        H A x 2
3) Static trace with animated marker, with or without visualiser   V A x 2
4) No trace but visualiser                                         H N  V
                                                                   V N  V
Not allowed:
    H N  N
    V N  N

trace in { hidden, visible, animated }
marker in { none, animated }
visualiser in { none, animated }


5) No sub-plot but visualiser (i.e.  need T, Y)

6) Y/Z plot but timing from elsewhere... T, Y, Z
'''
