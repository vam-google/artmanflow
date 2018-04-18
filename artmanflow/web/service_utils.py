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

import threading
from flask import render_template, current_app
from artmanflow.steps.common import ConfigUtils


class ServiceUtils:
    @staticmethod
    def stream_template(template_name, **context):
        current_app.update_template_context(context)
        template = current_app.jinja_env.get_template(template_name)
        stream = template.stream(context)
        stream.enable_buffering(10)
        return stream

    @staticmethod
    def get_step_default_config(config_file_name):
        default_config_str = render_template(config_file_name)
        default_config_yaml = ConfigUtils.read_config(
            yaml_str=default_config_str)
        return default_config_yaml

    @staticmethod
    def get_step_config(request_params, default_config_file_name,
        converter_func):
        default_config = ServiceUtils.get_step_default_config(
            default_config_file_name)
        extra_config = {'guest_root_path': default_config['guest_root_path']}
        return converter_func(request_params, extra_config)

    @staticmethod
    def run_host_step(step):
        HostScriptThread(step).start()


class HostScriptThread(threading.Thread):
    def __init__(self, step):
        threading.Thread.__init__(self)
        self._step = step

    def run(self):
        self._step.pre_execute()
        self._step.execute()