# -----------------------------------------------------------------------------
#
#  Cell Diagramming Language
#
#  Copyright (c) 2018  David Brooks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
# -----------------------------------------------------------------------------

import logging
import os

# -----------------------------------------------------------------------------

from cell_diagram.parser import Parser
import cell_diagram.geojson as GeoJSON

# -----------------------------------------------------------------------------


def parse(file, stylesheet=None):
    parser = Parser()
    return parser.parse(file, stylesheet)

# -----------------------------------------------------------------------------

def display_svg(file, geoson=False):
    (root, extension) =  os.path.splitext(file)
    if not extension:
        extension = '.xml'
    diagram = parse(root + extension)
    svg = diagram.svg()

    try:
        import OpenCOR as oc
        browser = oc.browserWebView()
        browser.setContent(svg, "image/svg+xml")
    except ImportError:
        f = open(root + '.svg', 'w')
        f.write(svg)
        f.close()

    if geoson:
        f = open(root + '.json', 'w')
        f.write(GeoJSON.dumps(diagram.geojson(), indent=2))
        f.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate SVG from a CellDL description.')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='show debugging')
    parser.add_argument('--geojson', action='store_true',
                        help='output features as GeoJSON')
    parser.add_argument('celldl', metavar='CELLDL_FILE',
                        help='the CellDl file')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    display_svg(args.celldl, args.geojson)

# -----------------------------------------------------------------------------
