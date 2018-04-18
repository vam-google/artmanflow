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

import subprocess
import os
import copy

from artmanflow.steps.common import HostStepProperties, ConfigUtils, BaseHost


class SourcesGenerationHost(BaseHost):
    def __init__(self, config):
        BaseHost.__init__(self, SourcesGenerationHost.host_step_properties(
            config['execution_id']), config)

    def execute(self):
        self._pull_docker_image()
        self._generate_sources_in_guest()
        return self._host.execution_id()

    def _pull_docker_image(self):
        with open(self._host.stdout_file_path(), 'a') as output_file:
            subprocess.call(['docker', 'pull', self._config['docker_image']],
                            stdout=output_file, stderr=output_file)
        return self._host.execution_id()

    def _generate_sources_in_guest(self):
        guest_config = copy.deepcopy(self._config)
        mounts = self._local_repo_mounts()
        extra_mounts = []
        for repo_name, repo_mounts in mounts.items():
            if repo_mounts:
                guest_config[repo_name]['git_repo'] = repo_mounts[1]
                extra_mounts.append(repo_mounts)

        self.run_guest_script(guest_config, extra_mounts)

    def _local_repo_mounts(self):
        config = self._config
        mounts = {
            'artman': self.local_repo_mount(config['artman']),
            'toolkit': self.local_repo_mount(config['toolkit']),
            'googleapis': self.local_repo_mount(config['googleapis'])
        }
        return mounts

    @staticmethod
    def host_step_properties(execution_id):
        return HostStepProperties(__file__, execution_id)


if __name__ == '__main__':
    execution_config = ConfigUtils.read_config(
        execution_id=ConfigUtils.generate_id('src-gen'))
    step = SourcesGenerationHost(execution_config)
    step.pre_execute()
    step.execute()
