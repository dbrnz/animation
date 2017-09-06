import io

import matplotlib
from matplotlib import pyplot as plt


POINTS_PER_INCH = 72.0


class Element(object):
    def __init__(self, id, trace, display, marker, visualiser):
        self._id = id
        self._trace = trace
        self._display = display
        self._marker = marker
        self._visualiser = visualiser

    def visualise(self, visualiser):
        self._visualiser = visualiser

class Animation(object):
    def __init__(self, start, end, step=0.0, speed=1.0, units='ms'):
        # step==0.==> step = period??
        # What though are units??
        if units not in ['ms', 's', 'm', 'h', 'd']:
            raise ValueError('Unknown units for timing')
        self._elements = {}
        self._next_id = 0

    def animate(self, trace, id=None, display='animate', marker=True, timing=None, visualiser=None):
        if display in [None, 'hidden', 'visible'] and not marker and visualiser is None:
            raise ValueError('Nothing to animate...')
        if id is None:
            id = 'trace_%s' % self._next_id
            self._next_id += 1
        self._elements[id] = Element(id, trace, display, marker, visualiser)
        return id

    def visualise(self, id, visualiser):
        self._animations[id].visualise(visualiser)


class Figure(matplotlib.figure.Figure):
    def __init__(self, *args, dpi=1200, tight_layout=True, **kwds):
        super().__init__(*args, dpi=dpi, **kwds)
        self._animations = {}
        self._script = []
        self._svg = []

    def add_script(self, script):
        self._script.append(script)

    def add_svg(self, svg):
        self._svg.append(svg)

    def save(self, filename, period=10, **kwds):  ## Period in ms
        svg = io.BytesIO()  # Save figure as SVG to an in-memory file
        super().savefig(filename, format='svg', **kwds)

        for trace on self._traces:
            plot = trace.axes
            # Transform world coordinates into SVG point-based coordinates
            trans_svg = (plot.transData.get_affine()
                                       .scale(POINTS_PER_INCH/self.dpi)
                                       .scale(1, -1)
                                       .translate(0, POINTS_PER_INCH*self.get_size_inches()[1]))
            xfm = trans_svg.get_matrix()
            self._script.append('animation.add_plot(new Plot(trace.id, new Transform1D(%f, %f), new Transform1D(%f, %f), \'%s\'));'
                                                                       % (xfm[0, 0], xfm[0, 2],    xfm[1, 1], xfm[1, 2],
                                                                          trace.visualiser if trace.visualiser else ''))

        # step == 0 ==> step = period
        # step *= speed

 73.83   398.49
  0.00   600.00

# 73.83pt = 72*(v_axis.transData.transform((0.0, v[0]))[0])/100  (pt/in)/(dots/in)

 = 72*102.545/100
Out[5]: array([ 102.54545455,   60.56943335])


def figure(**kwds):
    return plt.figure(FigureClass=Figure, **kwds)


Animation.save(period)

Element(start, end, step)

## Options to show marker, animate trace

## Option to only visualise (==> no plot/subplot, need to pass (t, y) arrays)


'''
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




if __name__ == '__main__':

    fig = figure()

    v_plot = fig.add_subplot(221, xlabel='Time (ms)', ylabel='Membrane voltage (mV)')
    v_trace = v_plot.plot(t, v, lw=1)[0]

    voltage = fig.animate(v_trace, visualiser='(t, y) => { voltage.setAttribute("r", (y + 90)/5); }')


    fig.save('test.svg')

'''
SVG added:


  <defs>
    <radialGradient id="ConcentrationGradient">
        <stop offset="10%" stop-color="red" />
        <stop offset="100%" stop-color="white" />
    </radialGradient>
  </defs>


  <circle id="concentration" cx="380" cy="80" r="5" fill="url(#ConcentrationGradient)"/>
  <circle id="voltage" cx="380" cy="220" r="5" fill="url(#ConcentrationGradient)"/>



    var voltage = svg.getElementById("voltage");


Generated:

  <script type="application/ecmascript" href="file:///Users/dave/build/SVG_Animation/animation.js"/>

  <script type="application/ecmascript"> <![CDATA[


    var animation = new Animation(0, 600, 5); // Time range

    var concentration = svg.getElementById("concentration");

    var sodium_plot = new Plot("Na", new Transform1D(0.5411, 73.83), (dy) => { concentration.setAttribute("r", 25 + 25*dy/200); });

    var voltage = svg.getElementById("voltage");
    var voltage_plot = new Plot("V", new Transform1D(0.5411, 73.83), (dy) => { voltage.setAttribute("r", 5 + 30*dy/200); })

    animation.add_plot(sodium_plot);
    animation.add_plot(voltage_plot);


    animation.start(10);

    ]]>
  </script>
'''
