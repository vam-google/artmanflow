# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re

class HtmlUtils:
    def __init__(self):
        pass

    _COLOR_REGEX = r'(\033\[\d*;*\d*m)'

    _COLOR_STYLE_MAP = {
        "\033[30m": "color:#000000;",
        "\033[0;30m": "color:#000000;",
        "\033[30;0m": "color:#000000;",
        "\033[31m": " color:#CD0000;",
        "\033[0;31m": "color:#CD0000;",
        "\033[31;0m": "color:#CD0000;",
        "\033[32m": "color:#00CD00;",
        "\033[0;32m": "color:#00CD00;",
        "\033[32;0m": "color:#00CD00;",
        "\033[33m": "color:#C4A000;",
        "\033[0;33m": "color:#C4A000;",
        "\033[33;0m": "color:#C4A000;",
        "\033[34m": "color:#0000EE;",
        "\033[0;34m": "color:#0000EE;",
        "\033[34;0m": "color:#0000EE;",
        "\033[35m": "color:#CD00CD;",
        "\033[0;35m": "color:#CD00CD;",
        "\033[35;0m": "color:#CD00CD;",
        "\033[36m": "color:#00CCCC;",
        "\033[0;36m": "color:#00CCCC;",
        "\033[36;0m": "color:#00CCCC;",
        "\033[37m": "color:#AAAAAA;",
        "\033[0;37m": "color:#AAAAAA;",
        "\033[37;0m": "color:#AAAAAA;",
        "\033[m": " ",
        "\033[0m": " ",
        "\033[1;30m": "color:#555555;font-weight:bold",
        "\033[30;1m": "color:#555555;font-weight:bold",
        "\033[1;31m": "color:#CD0000;font-weight:bold",
        "\033[31;1m": "color:#CD0000;font-weight:bold",
        "\033[1;32m": "color:#00CD00;font-weight:bold",
        "\033[32;1m": "color:#00CD00;font-weight:bold",
        "\033[1;33m": "color:#C4A000;font-weight:bold",
        "\033[33;1m": "color:#C4A000;font-weight:bold",
        "\033[1;34m": "color:#0000EE;font-weight:bold",
        "\033[34;1m": "color:#0000EE;font-weight:bold",
        "\033[1;35m": "color:#CD00CD;font-weight:bold",
        "\033[35;1m": "color:#CD00CD;font-weight:bold",
        "\033[1;36m": "color:#00CCCC;font-weight:bold",
        "\033[36;1m": "color:#00CCCC;font-weight:bold",
        "\033[1;37m": "color:#AAAAAA;font-weight:bold",
        "\033[37;1m": "color:#AAAAAA;font-weight:bold",
    }

    @staticmethod
    def generate_html_from_console_output(file_path):
        with open(file_path, 'r') as fl:
            yield '<pre>'
            color_regex = re.compile(HtmlUtils._COLOR_REGEX)
            for line in fl:
                yield HtmlUtils._read_line(color_regex, line)
            yield '</pre>'
            # yield '</body></html>'

    @staticmethod
    def generate_output_link(file_url, link_name):
        yield "<p><a href='%s'>%s</a></p>" % (file_url, link_name)

    @staticmethod
    def _read_line(regex, line):
        split_line = regex.split(line)
        split_len = len(split_line)

        res = []
        for i in range(0, split_len, 2):
            res.append(split_line[i])

            if i + 1 < split_len:
                style = HtmlUtils._COLOR_STYLE_MAP.get(split_line[i + 1])
                if style:
                    res.append("</pre><pre style='display:inline;%s'>" % style)
                else:
                    res.append(split_line[i + 1])

        if split_len > 1:
            last_token = split_line[split_len - 1]
            if not last_token or last_token.isspace():
                res.append('\n')

        return ''.join(res)
