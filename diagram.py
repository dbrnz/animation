import numpy as np
from math import cos, sin, asin, pi

def c2e(c, r, phi, theta, d_theta):
    A = np.matrix([[cos(phi), -sin(phi)], [sin(phi), cos(phi)]])
    R0 = r*np.matrix([cos(theta), sin(theta)]).transpose()
    R1 = r*np.matrix([cos(theta+d_theta), sin(theta+d_theta)]).transpose()
    C = np.matrix(c).transpose()
    P0 = A*R0 + C
    p1 = A*R1 + C - P0
    return list(P0.flat) + list(p1.flat)


phi = 270*pi/180


def path(r, d_theta, dirn):
    dt = d_theta*pi/180
    R = r/asin(dt/2)
    path = ['M0,0']
    t = 0
    while t <= pi/2:
        n = c2e((0, R), R, phi, t, dt)[2:]
        path.append('a0,0 0 0,1 %g,%g' % tuple(n))
        t += dt
    return '''<g transform="translate(300, %g)">
    <path stroke="purple" fill="none" marker-mid="url(#corner-%s)"
          d="%s"/>
</g>''' % (100 + (50-R), dirn, '\n'.join(path))

## 2.8 = 2.4 + 0.5 - 0.1
## radius + stroke-width/2.0 - overlap
## Outer perimeter
print(path(2.8, 10,, 'in'))

## Inner perimeter
print(path(2.8, 30, 'out'))
