from lxml import etree
import json

from tornado.httpclient import HTTPRequest, HTTPClient, HTTPError

## TODO: Use AsyncHTTPClient

def suffix_ids(xml, attribute, id_base, new_attrib=None):
    for e in xml.findall('.//*[@{}]'.format(attribute)):
        if new_attrib is None:
            e.attrib[attribute] += '_' + id_base
        else:
            e.attrib[new_attrib] = e.attrib[attribute] + '_' + id_base
            del e.attrib[attribute]

def clean_svg(svg, id_base):
    if not svg.startswith(b'<svg '):
        raise ValueError(svg)
    xml = etree.fromstring(svg)
    xml.tag = '{http://www.w3.org/2000/svg}g'
    w = xml.attrib.get('width', None)
    h = xml.attrib.get('height', None)
    s = xml.attrib.get('style', 'N 0').split()
    va = s[1][:-1] if s[0] == 'vertical-align:' else None
    vb = xml.attrib.get('viewBox', None)
    xml.attrib.clear()
    title = xml.find('{http://www.w3.org/2000/svg}title')
    if title is not None:
        xml.remove(title)
    suffix_ids(xml, 'id', id_base)
    suffix_ids(xml, '{http://www.w3.org/1999/xlink}href', id_base) ## , new_attrib='href)  ## SVG 2 only
    return (etree.tostring(xml, encoding='unicode'), (w, h, va, vb))

def typeset(latex, id_base):
    if latex.startswith('$') and latex.endswith('$'):
        latex = latex[1:-1]
    mathjax = json.dumps({
        'format': 'TeX',
        'math': latex,
        'svg':True,
##        'ex': 6,   ###  ?????
        'width': 10000,
        'linebreaks': False,
    });
    headers = { 'Content-Type': 'application/json' }
    request = HTTPRequest('http://localhost:8003/',
                          method='POST',
                          headers=headers,
                          body=mathjax)
    http_client = HTTPClient()

    try:
        response = http_client.fetch(request)
        svg = clean_svg(response.body, id_base)
    except HTTPError as e:
        # HTTPError is raised for non-200 responses; the response
        # can be found in e.response.
        svg = '<text>ERROR 1</text>'
    except IOError as e:
        # Other errors are possible, such as IOError.
        svg = '<text>ERROR 2</text>'
    http_client.close()

    return svg


if __name__ == '__main__':
    print(typeset('a', 'ID'))
