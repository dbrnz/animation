
import OpenCOR as oc

s = oc.simulation()
d = s.data()
r = s.results()

d.setEndingPoint(600)
s.run()

t = r.points().values()
v = r.states()['membrane/V'].values()
na = r.states()['sodium_dynamics/Na_i'].values()


from matplotlib import pyplot as plt

na_axis = plt.subplot(2, 1, 1)
na_plot = plt.plot(t, na, lw=1)
na_plot[0].set_gid('Na')
plt.ylabel('Na_i (millimolar)')

v_axis = plt.subplot(2, 1, 2)
v_plot = plt.plot(t, v, lw=1)
v_plot[0].set_gid('V')
plt.ylabel('Membrane voltage (mV)')
plt.xlabel('Time (ms)')

#plt.show()

#plt.savefig('sodium.svg')


v_axis.transData.transform((0.0, v[0]))
Out[5]: array([ 102.54545455,   60.56943335])

na_axis.transData.transform((0.0, na[0]))
Out[8]: array([ 102.54545455,  355.28186559])

plt.figure().transFigure.transform((1, 1))
Out[20]: array([ 640.,  480.])


72*102.54545455/100
Out[24]: 73.832727276     ## This is x-coord of t[0] in SVG

72*(480 - 60.56943335)/100
Out[30]: 301.990007988    ## This is y-coord of V[0] in SVG

72*(480 - 355.281865595)/100
Out[31]: 89.7970567716    ## This is y-coord of Na[0] in SVG


# What if sub-plots horizontal ??

na_axis = plt.subplot(1, 2, 1)
na_plot = plt.plot(t, na, lw=1)
na_plot[0].set_gid('Na')
plt.ylabel('Na_i (millimolar)')

v_axis = plt.subplot(1, 2, 2)
v_plot = plt.plot(t, v, lw=1)
v_plot[0].set_gid('V')
plt.ylabel('Membrane voltage (mV)')
plt.xlabel('Time (ms)')
Out[15]: <matplotlib.text.Text at 0x12927b668>

plt.show()

plt.figure().transFigure.transform((1, 1))
Out[17]: array([ 640.,  480.])

v_axis.transData.transform((0.0, v[0]))
Out[18]: array([ 360.79338843,   71.64007221])
   <g id="V">
    <path clip-path="url(#pa986f9d7a4)" d="M 259.77124 295.277218

na_axis.transData.transform((0.0, na[0]))
Out[2]: array([  90.24793388,  274.74010429])
   <g id="Na">
    <path clip-path="url(#p0afa45cc6c)" d="M 64.978512 147.787125

# Set time range and period from Python
# plot path drawing to scale time (using scale factors passed from Python)??
# Then visualise call to have real world values (t, y)

