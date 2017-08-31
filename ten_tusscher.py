
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

plt.subplot(2, 1, 1)
na_plot = plt.plot(t, na, lw=1)
na_plot[0].set_gid('Na')
plt.ylabel('Na_i (millimolar)')

plt.subplot(2, 1, 2)
v_plot = plt.plot(t, v, lw=1)
v_plot[0].set_gid('V')
plt.ylabel('Membrane voltage (mV)')
plt.xlabel('Time (ms)')

plt.show()

plt.savefig('sodium.svg')
