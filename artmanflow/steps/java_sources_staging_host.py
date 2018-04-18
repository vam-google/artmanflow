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

import copy

from artmanflow.steps.common import HostStepProperties, ConfigUtils, BaseHost


class JavaSourcesStagingHost(BaseHost):
    def __init__(self, config):
        BaseHost.__init__(self, JavaSourcesStagingHost.host_step_properties(
            config['execution_id']), config)

    def execute(self):
        self._stage_sources_in_guest()
        return self._host.execution_id()

    def _stage_sources_in_guest(self):
        host_art_path = self._config['generator_artifacts']['sources_zip']
        art_name = host_art_path[host_art_path.rfind('/') + 1:]
        guest_art_path = self._guest.guest_root_subpath(art_name)

        guest_config = copy.deepcopy(self._config)
        guest_config['generator_artifacts']['sources_zip'] = guest_art_path

        self.run_guest_script(guest_config,
                              [[host_art_path, guest_art_path, 'ro']])

    @staticmethod
    def host_step_properties(execution_id):
        return HostStepProperties(__file__, execution_id)


if __name__ == '__main__':
    execution_config = ConfigUtils.read_config(
        execution_id=ConfigUtils.generate_id('java-src-stage-'))
    step = JavaSourcesStagingHost(execution_config)
    step.pre_execute()
    step.execute()
