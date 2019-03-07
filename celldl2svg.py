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

# -----------------------------------------------------------------------------


def parse(file, stylesheet=None):
    parser = Parser()
    return parser.parse(file, stylesheet)

# -----------------------------------------------------------------------------

def display_svg(file):
    (root, extension) =  os.path.splitext(file)
    if not extension:
        extension = '.xml'
    try:
        diagram = parse(root + extension)
        svg = diagram.svg()
    except Exception as msg:
        print('ERROR: {}',format(msg))
        sys.exit(1)
    try:
        import OpenCOR as oc
        browser = oc.browserWebView()
        browser.setContent(svg, "image/svg+xml")
    except ImportError:
        f = open(root + '.svg', 'w')
        f.write(svg)
        f.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate SVG from a CellDL description.')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='show debugging')
    parser.add_argument('celldl', metavar='CELLDL_FILE',
                        help='the CellDl file')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    display_svg(args.celldl)

# -----------------------------------------------------------------------------
