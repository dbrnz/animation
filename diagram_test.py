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

from cell_diagram.parser import Parser

# -----------------------------------------------------------------------------


def parse(file, stylesheet=None):
    parser = Parser()
    return parser.parse(file, stylesheet)

# -----------------------------------------------------------------------------

def display_svg(file):
    try:
        diagram = parse('{}.xml'.format(file))
        svg = diagram.svg()
    except Exception as msg:
        raise
        print('ERROR: {}',format(msg))
        sys.exit(1)
    try:
        import OpenCOR as oc
        browser = oc.browserWebView()
        browser.setContent(svg, "image/svg+xml")
    except ImportError:
        f = open('{}.svg'.format(file), 'w')
        f.write(svg)
        f.close()


if __name__ == '__main__':
    import sys

    import logging
    # logging.getLogger().setLevel(logging.DEBUG)

    display_svg('cell_diagram')

# -----------------------------------------------------------------------------
