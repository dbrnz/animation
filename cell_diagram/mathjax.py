from subprocess import Popen, PIPE, STDOUT

from lxml import etree

def suffix_ids(xml, attribute, id_base, new_attrib=None):
    for e in xml.findall('.//*[@{}]'.format(attribute)):
        if new_attrib is None:
            e.attrib[attribute] += '_' + id_base
        else:
            e.attrib[new_attrib] = e.attrib[attribute] + '_' + id_base
            del e.attrib[attribute]

def typeset(latex, id_base):
    with Popen(['node', 'mathjax.js'], bufsize=1, universal_newlines=True,
               stdin=PIPE, stdout=PIPE, stderr=STDOUT) as proc:
        print("TS:", latex)
        proc.stdin.write('{}\n'.format(latex))
        svg = proc.stdout.read()
        if not svg.startswith('<svg '):
            raise ValueError(svg)
        xml = etree.fromstring(svg)
        xml.tag = '{http://www.w3.org/2000/svg}g'
        xml.attrib.clear()
##'width': '1.23ex', 'height': '1.676ex', 'style': 'vertical-align: -0.338ex;', 'viewBox': '0 -576.1 529.5 721.6'
        title = xml.find('{http://www.w3.org/2000/svg}title')
        if title is not None:
            xml.remove(title)
        suffix_ids(xml, 'id', id_base)
        suffix_ids(xml, '{http://www.w3.org/1999/xlink}href', id_base, new_attrib='href')
        return etree.tostring(xml, encoding='unicode')


if __name__ == '__main__':
    print(typeset('a', 'ID'))
