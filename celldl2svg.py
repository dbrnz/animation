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

from cell_diagram.svg_elements import DefinesStore
# -----------------------------------------------------------------------------


def parse(file, stylesheet=None):
    parser = Parser()
    return parser.parse(file, stylesheet)

# -----------------------------------------------------------------------------

def export_diagram_layer(diagram, layer, file_path, geojson=False, excludes=None):
    file_name = '{}-{}'.format(file_path, layer) if layer else file_path

    svg = diagram.generate_svg(layer, excludes=excludes)
    f = open('{}.svg'.format(file_name), 'w')
    f.write(svg)
    f.close()

    if geojson:
        json = diagram.generate_geojson(layer, excludes=excludes)
        f = open('{}.json'.format(file_name), 'w')
        f.write(GeoJSON.dumps(json, indent=2))
        f.close()


def main(file, geojson=False, classes=None):
    (root, extension) = os.path.splitext(file)
    if not extension:
        extension = '.xml'

    diagram = parse(root + extension)

    if classes:
        defines_top = DefinesStore.top()
        export_diagram_layer(diagram, None, root, geojson, excludes=frozenset(classes))
        for cls in classes:
            DefinesStore.reset(defines_top)
            export_diagram_layer(diagram, cls, root, geojson)
    else:
        try:
            import OpenCOR as oc
            svg = diagram.svg()
            browser = oc.browserWebView()
            browser.setContent(svg, "image/svg+xml")
        except ModuleNotFoundError:
            export_diagram_layer(diagram, None, root, geojson)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate SVG from a CellDL description.')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='show debugging')
    parser.add_argument('--geojson', action='store_true',
                        help='output features as GeoJSON')
    parser.add_argument('--layer-classes', dest='classes', metavar='CLASS', nargs='+',
                        help='break SVG into separate files by classes')
    parser.add_argument('--celldl', metavar='CELLDL_FILE',
                        help='the CellDl file')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    main(args.celldl, args.geojson, args.classes)

# -----------------------------------------------------------------------------
