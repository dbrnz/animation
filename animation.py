import io

import matplotlib
from matplotlib import pyplot as plt


POINTS_PER_INCH = 72.0

class Visualiser(object):
    def __init__(self, id, position, setup_js, call_js):
        self._id = id
        self._position = position   # (x, y) on Axes scale??
        self._setup_js = setup_js
        self._call_js = call_js

    def get_pos(self, plot):
        fig = plot.get_figure()
        trans_vis = (plot.transAxes.get_affine()
                                   .frozen()
                                   .scale(POINTS_PER_INCH/fig.dpi)
                                   .scale(1, -1)
                                   .translate(0, POINTS_PER_INCH*fig.get_figheight()))
        return trans_vis.transform(self._position)

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
        return '<circle id="%(id)s" cx="%(cx)g" cy="%(cy)g" r="0" fill="%(fill)s"/>' % dict(
            id=self._id, cx=pos[0], cy=pos[1], fill=self._fill)


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
        self._svg = []

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

    def add_svg(self, svg):
        self._svg.append(svg)

    def generate_svg(self, filename, start, end, step=0.0, speed=1.0, units='ms', period=10, **kwds):  ## Period in ms
        if units not in ['ms', 's', 'm', 'h', 'd']:
            raise ValueError('Unknown timing units')

        ## Allow for units and scale everything?? Adjust speed ???
        if step == 0: step = period
        step *= speed

        self.add_script('var animation = new Animation(%g, %g, %g);' % (start, end, step))

        # First create SVG before using transforms since backend can adjust them

#        svg = io.BytesIO()  # Save figure as SVG to an in-memory file
#        super().savefig(svg, format='svg', **kwds)
        super().savefig(filename, format='svg', **kwds)


        for animation in self._animations:
            trace = animation.trace
            plot = trace.axes
            # Transform world coordinates into SVG point-based coordinates
            trans_svg = (plot.transData.get_affine()
                                       .frozen()
                                       .scale(POINTS_PER_INCH/self.dpi)
                                       .scale(1, -1)
                                       .translate(0, POINTS_PER_INCH*self.get_figheight()))
            xfm = trans_svg.get_matrix()

            if animation.visualiser:
                self.add_svg(animation.visualiser.svg(plot))
                self.add_script(animation.visualiser.setup_js())
                invoke_visualiser = ', %s' % animation.visualiser.call_js()
            else:
                invoke_visualiser = ''

            self.add_script('animation.add_trace(new Trace("%s", new Transform1D(%f, %f), new Transform1D(%f, %f) %s));'
                                                % (animation.id,    xfm[0, 0], xfm[0, 2],    xfm[1, 1], xfm[1, 2],
                                                                                                        invoke_visualiser))
        self.add_script('animation.start(%g);' % period)

        self._script.insert(0, '<script type="application/ecmascript"> <![CDATA[')
        self._script.append(']]></script>')
        self.add_svg('\n'.join(self._script))


        # Need to write this just before end of `svg` file and then save to disk...
        print('\n'.join(self._svg))


def figure(**kwds):
    return plt.figure(FigureClass=Figure, tight_layout=True, **kwds)



if __name__ == '__main__':

    t  = [0, 1, 2, 3, 4, 5, 6, 7, 7, 9]
    v  = [0, 1, 2, 3, 4, 4, 3, 2, 1, 0]
    na = [9, 8, 7, 6, 5, 4, 5, 6, 7, 8]


    fig = figure()

    fig.add_svg('''<defs>
      <radialGradient id="RedGradient">
          <stop offset="10%" stop-color="red" />
          <stop offset="100%" stop-color="white" />
      </radialGradient>
    </defs>
    <script type="application/ecmascript" href="file:///Users/dave/build/SVG_Animation/animation.js"/>
    ''')

    sodium_visualiser = CircleVisualiser('sodium', (0.9, 0.8),
                                          'url(#RedGradient)',
                                          'var sodium = svg.getElementById("sodium");',
                                          '(t, y) => { sodium.setAttribute("r", 600*(y - 8.59)); }')
    sodium_plot = fig.add_subplot(211, xlabel='Time (ms)', ylabel='Na i (millimolar)')
    sodium_trace = sodium_plot.plot(t, na, lw=1)[0]
    fig.add_animation(sodium_trace, visualiser=sodium_visualiser)

    voltage_visualiser = CircleVisualiser('voltage', (0.9, 0.8),
                                          'url(#RedGradient)',
                                          'var voltage = svg.getElementById("voltage");',
                                          '(t, y) => { voltage.setAttribute("r", (y + 90)/5); }')
    voltage_plot = fig.add_subplot(212, xlabel='Time (ms)', ylabel='Membrane voltage (mV)')
    voltage_trace = voltage_plot.plot(t, v, lw=1)[0]   ## Set colour...
    fig.add_animation(voltage_trace, visualiser=voltage_visualiser)

    fig.generate_svg('test.svg', 0, 600, speed=0.5)

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
