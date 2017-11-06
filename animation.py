import io
from lxml import etree as ET
import numpy as np

import matplotlib
##matplotlib.use('svg')  ## Otherwise transforms are wrong with tight-layout...

from matplotlib import pyplot as plt

from matplotlib import _path
from matplotlib.path import Path
from matplotlib.transforms import Affine2D


POINTS_PER_INCH = 72.0

# Diagram SVG definitions

DIAGRAM_ANIMATION_SVG = '''
  <defs xmlns:xlink="http://www.w3.org/1999/xlink">
    <g id="IonCurrent">
      <circle cy="0"   r="15"/>
      <circle cy="30"  r="15"/>
      <circle cy="60"  r="15"/>
      <circle cy="90"  r="15"/>
      <circle cy="120" r="15"/>
      <circle cy="150" r="15"/>
      <circle cy="180" r="15"/>
    </g>
    <linearGradient x1="0" x2="0" y1="0" y2="200" gradientUnits="userSpaceOnUse" id="IonMaskGradient">
      <stop offset="0" stop-color="white" stop-opacity="0.1"/>
      <stop offset="0.5" stop-color="white" stop-opacity="1"/>
      <stop offset="1" stop-color="white" stop-opacity="1"/>
    </linearGradient>
    <mask width="20" height="200" x="0" y="0" maskmaskUnits="userSpaceOnUse" id="IonMask">
      <ellipse cy="100" rx="40" ry="110" fill="url(#IonMaskGradient)"/>
    </mask>
    <clipPath id="IonMaskClipPath">
      <ellipse cy="100" rx="40" ry="100"/>
    </clipPath>
    <g id="IonChannel">
      <g mask="url(#IonMask)">
        <use xlink:href="#IonCurrent"/>
      </g>
    </g>
  </defs>
'''

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

    class IonChannel {
      constructor(id) {
        this.channel = svg.getElementById(id);
        this.last_time = 0;
        this.offset = -15;
      }
      paint(time, current) {
        if (this.channel) {
          var dt = time - this.last_time;  // seconds
          if (dt > 0.0) {
            this.offset += 300*dt*current; // current == 1.0  ==> offset changes by 30px in 100ms
            if (this.offset > 15.0) this.offset = -15.0;
            this.channel.setAttribute("y", this.offset);
          }
        this.last_time = time;
        }
      }
    }

    class Visualiser {
      constructor(id, radius_fn) {
        this.visualiser = svg.getElementById(id);
        this.radius_fn = radius_fn;
      }
      paint(time, value) {
        if (this.visualiser) {
          var radius = this.radius_fn(time, value);
          this.visualiser.setAttribute("r", radius);
        }
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

      paint(time_from, time_to) {
        var mx, my;
        var path = "";
        var xy = this.points;
        var start = this.time_transform.transform(time_from);
        var t = this.time_transform.transform(time_to);

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
          if (this.line)
            path = "M " + String(mx) + " " + String(my);
          if (t > xy[i]) {
            i += 2;
            while (i < xy.length && xy[i] <= t) {
              mx = xy[i]; my = xy[i+1];
              if (i == 2) path += " L";
              if (this.line)
                path += " " + String(mx) + " " + String(my);
              i += 2;
            }
            if (i < xy.length) {  // xy[i-2] <= t < xy[i]
              var dt = t - xy[i-2];
              var dy = dt*(xy[i+1]-xy[i-1])/(xy[i]-xy[i-2]);
              mx = t; my = xy[i-1] + dy;
              if (this.line)
                path += " l" + String(dt) + " " + String(dy);
            }
          }
          if (this.visualiser)
            this.visualiser.paint(time_to, this.value_transform.inverse(my));
        }
        if (this.line) {
          if (path == "") {
            this.marker.setAttribute("visibility", "hidden");
          } else {
            this.line.setAttribute("d", path);
            this.marker.setAttribute("cx", mx);
            this.marker.setAttribute("cy", my);
            this.marker.setAttribute("visibility", "visible");
          }
        }
      }
    };

    class Animation {
      constructor(start, end) {
        this.start_time = start;
        this.end_time = end;
        this.time = this.start_time;
        this.animation = null;
        this.traces = [];
        this.millisecs = 0;
        this.speed = 1.0;
      }
      add_trace(trace) {
        this.traces.push(trace);
      }
      paint_traces() {
        for (let trace of this.traces)
          trace.paint(this.start_time, this.time);
      }
      animate() {
        var dt = Date.now() - this.millisecs;
        this.millisecs = Date.now();
        this.paint_traces();
        this.time += dt*this.speed/1000.0;
        if (this.time > this.end_time) this.time = this.start_time;
      }
      start(speed, period) {
        this.speed = speed;
        if (this.animation == null)
          this.animation = setInterval(this.animate.bind(this), period);
        this.millisecs = Date.now();
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
    def __init__(self, id, position, setup_js='', call_js=''):
        self._id = id
        self._position = position   # (x, y) on Axes scale??
        self._setup_js = setup_js
        self._call_js = call_js

    @property
    def id(self):
        return self._id

    def get_pos(self, plot):
        return plot.get_figure().make_flip_transform(plot.transAxes).transform(self._position)

    def setup_js(self):
        return self._setup_js

    def call_js(self):
        return self._call_js

    def script(self):
        return ''

    def svg(self, plot):
        pass

class CircleVisualiser(Visualiser):
    def __init__(self, id, position, fill, **kwds):
        super().__init__(id, position, **kwds)
        self._fill = fill

    def svg(self, plot):
        ## Add any SVG for self._fill ??
        pos = self.get_pos(plot)
        return ET.Element('circle',
                          dict(id=self._id, cx='%g' % pos[0], cy='%g' % pos[1], r='0', fill=self._fill))

class ChannelVisualiser(Visualiser):
    def __init__(self, id, position, direction, colour, t, y):
        super().__init__(id, position)
        self._direction = direction
        self._colour = colour

        # Scale y values so absolute maximum becomes 1
        maxabs = y[np.argmax(abs(y))]
        if maxabs != 0.0: y /= maxabs

        xy = np.empty((len(t), 2), dtype=np.float_)
        xy[:, 0] = t
        xy[:, 1] = y

        # Create a simplified path, scaled to ensure it will have a resonable number of points
        scale = 1000.0/abs(t[1] - t[0])
        xfm = Affine2D().scale(scale, scale)
        simplified = Path(xy).cleaned(transform=xfm, simplify=True)

        # Generate the SVG path, transforming back to the original data values
        self._path = _path.convert_to_string(simplified.transformed(xfm.inverted()), None, None, False, None, 6, [b'M', b'L', b'Q', b'C', b'z'], False).decode('ascii')

    def xml(self):
        transform = ["translate({xpos}, {ypos})".format(xpos=self._position[0], ypos=self._position[1])]
        if self._direction[-1] == '-':
            transform.append("rotate(180 0 20)")
        transform.append("scale(0.2)")
        return [ET.XML('''<g xmlns:xlink="http://www.w3.org/1999/xlink" transform="{transform}">
                            <use xlink:href="#IonChannel" fill="{colour}" x="0" id="{id}_channel"/>
                          </g>'''.format(transform=' '.join(transform), colour=self._colour, id=self._id)),
                ET.XML('<defs><path id="{id}_data_path" d="{d}"/></defs>'.format(id=self._id, d=self._path))
                ]

    def script(self):
        return 'new Trace("{id}_data", null, null, new IonChannel("{id}_channel"))'.format(id=self._id)

class Animation(object):
    def __init__(self, id, trace, display, marker, visualiser):
        trace.set_gid(id)
        self.id = id
        self.trace = trace
        self.display = display
        self.marker = marker
        self.visualiser = visualiser

class Diagram(object):
    def __init__(self, diagram_file, simulation, start_time, end_time, units='ms'):
        if units not in ['ms', 's', 'm', 'h', 'd']:
            raise ValueError('Unknown timing units')
        self._svg_tree = ET.parse(diagram_file)
        self._times = simulation.results().dataStore().voi().values()
        self._start_index = np.searchsorted(self._times, start_time)
        self._end_index = np.searchsorted(self._times, end_time) + 1
        self._variables = simulation.results().dataStore().variables()
        self._script = [ ]
        self._script.append(ANIMATION_SCRIPT)
        self._script.append('var animation = new Animation({start}, {end});'
                            .format(start=start_time, end=end_time))
        self._xml = [ ]
        self._xml.append(ET.XML(DIAGRAM_ANIMATION_SVG))

    def add_channel(self, variable_id, element_id, position, direction, colour):
        # Get the SVG element
        element = self._svg_tree.find('//*/svg:g[@id="{id}"]'.format(id=element_id),
                                      {'svg': 'http://www.w3.org/2000/svg'})
        # And the corresponding simulation variable
        variable = self._variables.get(variable_id)

        if element is not None and variable is not None:
            channel = ChannelVisualiser(element_id, position, direction, colour,
                                        self._times[self._start_index:self._end_index],
                                        variable.values()[self._start_index:self._end_index])
            element.extend(channel.xml())
            self._script.append('animation.add_trace({trace});'.format(trace=channel.script()))

    def generate_svg(self, speed, period):  #  `period` in milliseconds
        self._script.append('animation.start({speed}, {period});'.format(speed=speed, period=period))
        script_element = ET.Element('script', {'type': 'application/ecmascript'})
        script_element.text = '<![CDATA[{code}]]>'.format(code='\n'.join(self._script))
        self._xml.append(script_element)

        self._svg_tree.getroot().extend(self._xml)

        # Return SVG as a Unicode string. A method of 'html' ensures
        # that '<', '>' and '&' are not escaped.
        return ET.tostring(self._svg_tree, encoding='unicode', method='html')

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
# Use trace to get range etc of visualiser...
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

    def generate_svg(self, start, end, step, units='ms', speed=1.0, **kwds):  ## Period in ms
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
            '''
            p = path.find('../..')
            p.getparent().remove(p)
'''
            # Affine matrix to transform world coordinates into SVG point-based coordinates
            xfm = self.make_flip_transform(plot.transData).get_matrix()

            if animation.visualiser:
## Where we can auto-calculate visualisers...
                self.add_xml(animation.visualiser.svg(plot))
## Replace by "new Visualiser(id)"
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


if __name__ == '__main__':

    import OpenCOR as oc
    '''
    s = oc.openSimulation('noble_1962.cellml')
    s.data().setEndingPoint(0.6)
    s.data().setPointInterval(0.005)
    s.reset()
    s.run()
'''
    s = oc.simulation()

    diagram = Diagram('noble_1962.svg', s, 0.04, 0.60, 's')

    diagram.add_channel('sodium_channel/i_Na', 'i_Na', (183.849, 49.756), 'V', 'red')
    diagram.add_channel('potassium_channel/i_K', 'i_K', (80.867, 49.756), 'V-', '#b666d2')
    diagram.add_channel('leakage_current/i_Leak', 'i_Leak', (133.551, 167.485), 'V', 'orange')

    svg = diagram.generate_svg(speed=0.5, period=25)

    browser = oc.browserWebView()
    browser.setContent(svg, "image/svg+xml")

    f = open('noble_1962_animated.svg', 'w')
    f.write(svg)
    f.close()

    '''
#    svg = animate_diagram('ten_tusscher_2004.svg', s, {'sodium_dynamics/Na_i': 'i_Na'}, 0, 1000, 10)

'i_up'
'i_leak'
'i_rel'
'i_Kr'
'i_Ks'
'i_K1'
'i_to'
'i_p_K'

'sodium_dynamics/Na_i',
'i_Na'

'i_b_Na'
'i_CaL'
'i_b_Ca'
'i_p_Ca'
'i_NaCa'
'i_NaK'


'calcium_dynamics/Ca_SR',
'transient_outward_current/transient_outward_current_s_gate/s',
'rapid_time_dependent_potassium_current/rapid_time_dependent_potassium_current_Xr1_gate/Xr1',
'fast_sodium_current/fast_sodium_current_j_gate/j',
'L_type_Ca_current/L_type_Ca_current_f_gate/f',
'calcium_dynamics/g',
'transient_outward_current/transient_outward_current_r_gate/r',
'L_type_Ca_current/L_type_Ca_current_d_gate/d',
'L_type_Ca_current/L_type_Ca_current_fCa_gate/fCa',
'potassium_dynamics/K_i',
'calcium_dynamics/Ca_i',
'fast_sodium_current/fast_sodium_current_h_gate/h',
'rapid_time_dependent_potassium_current/rapid_time_dependent_potassium_current_Xr2_gate/Xr2',
'slow_time_dependent_potassium_current/slow_time_dependent_potassium_current_Xs_gate/Xs',
'fast_sodium_current/fast_sodium_current_m_gate/m'])
'''

else:
    t  = [0, 1, 2, 3, 4, 5, 6, 7, 7, 9, 10]
    v  = [0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 0]
    na = [9, 8, 7, 6, 5, 4, 5, 6, 7, 8, 9]

    fig = figure()

    fig.add_script(ANIMATION_SCRIPT)

## Add standard gradients as they are used...
    fig.add_xml(ET.XML('''<defs>
      <radialGradient id="RedGradient">
          <stop offset="10%" stop-color="red" />
          <stop offset="100%" stop-color="white" />
      </radialGradient>
    </defs>'''))

    sodium_visualiser = CircleVisualiser('sodium', (0.95, 0.8),
                                          'url(#RedGradient)',
                                          setup_js='var sodiumVar = svg.getElementById("sodium");',
#                                          call_js= '(t, y) => { voltageVar.setAttribute("r", 5*(y-3)); }')
## Get range and use this to set default function for radius...
                                          call_js='(t, y) => { sodiumVar.setAttribute("r", 5*(y-2)); }')
#                                          call_js='(t, y) => { sodiumVar.setAttribute("r", 600*(y - 8.59)); }')


    sodium_plot = fig.add_subplot(211, xlabel='Time (ms)', ylabel='Na i (millimolar)')
    sodium_trace = sodium_plot.plot(t, na, lw=1)[0]
    fig.add_animation(sodium_trace, visualiser=sodium_visualiser)
                                 #  visualiser=CircleVisualiser(colour=??))

    voltage_visualiser = CircleVisualiser('voltage', (0.95, 0.8),
                                          'url(#RedGradient)',
                                          setup_js='var voltageVar = svg.getElementById("voltage");',
                                          call_js='(t, y) => { voltageVar.setAttribute("r", 5*(y+1)); }')
#                                          call_js='(t, y) => { voltageVar.setAttribute("r", (y + 90)/5); }')

    voltage_plot = fig.add_subplot(212, xlabel='Time (ms)', ylabel='Membrane voltage (mV)')
    voltage_trace = voltage_plot.plot(t, v, lw=1)[0]   ## Set colour...
    fig.add_animation(voltage_trace, visualiser=voltage_visualiser)

## Auto determine max T and speed
    svg = fig.generate_svg(0, 10, 1, speed=0.1)
## 600, 0.5
    fig.close()


#    f = open('test.svg', 'w')
#    f.write(svg)
#    f.close()

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
