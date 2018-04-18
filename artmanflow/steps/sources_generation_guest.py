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

import os

try:
    from common import GuestStepProperties, ConfigUtils, GitUtils, BaseGuest
except ImportError:
    from artmanflow.steps.common import \
        GuestStepProperties, ConfigUtils, GitUtils, BaseGuest


class SourcesGenerationGuest(BaseGuest):
    def execute(self):
        try:
            self.before_execute()
            repo_names = self._checkout_git_repos()
            self._reinstall_components(repo_names)
            self._run_artman(repo_names)
            self._fix_generator_output()
            self._archive_artifacts()
            self.after_execute(self._config['debug_mode'])
        except Exception as e:
            self.after_execute(True, e)
            raise

    def _checkout_git_repos(self):
        repo_names = {
            'artman': self.checkout_git_input_repo(self._config['artman']),
            'toolkit': self.checkout_git_input_repo(self._config['toolkit']),
            'googleapis': self.checkout_git_input_repo(
                self._config['googleapis'])
        }
        return repo_names

    def _reinstall_components(self, repo_names):
        self.run_command(
            ['pip3', 'uninstall', '--yes', '-q', 'googleapis-artman'])
        self.run_command(['pip3', 'install', '-q', '-e',
                          self._guest.guest_root_subpath('artman')])
        self.run_command(['rm', '-rf', '/artman'])
        self.run_command(['rm', '-rf', '/googleapis'])
        self.run_command(['rm', '-rf', '/toolkit'])

        self._guest.guest_root_subpath('toolkit')
        artman_config = {
            'local': {
                'toolkit': self._guest.guest_root_subpath(repo_names['toolkit'])
            }
        }
        ConfigUtils.dump_config(artman_config, '/root/.artman/config.yaml')
        # self._docker.run_command(['cat', '/root/.artman/config.yaml'])

    def _run_artman(self, repo_names):
        apis = self._config['artman_client_yaml_configs']

        for api in apis:
            path = self._guest.guest_client_yaml_file_path(api['path'])
            api_name = path.partition('/artman_')[2].partition('.yaml')[0]

            target = api['target'].split(',')
            if len(target) == 1:
                target.insert(0, 'generate')

            args = [
                '--root-dir',
                self._guest.guest_root_subpath(repo_names['googleapis']),
                '--config', self._guest.guest_root_subpath(api['path']),
                '--output-dir',
                self._guest.guest_output_dir_subpath('artifacts'),
                '--local'
            ]

            verbose = ['-v'] if self._config['debug_mode'] else []
            self.puts("\n> Generating API %s" % api_name)
            self.run_command(
                ['python3', '-m', 'artman.cli.main'] + args + verbose + target,
                self._guest.guest_root_subpath(repo_names['artman']))

    def _archive_artifacts(self):
        self.run_command(['tar', '-pzcf', 'artifacts.tar.gz',
                          '--remove-files', '-C', 'artifacts', '.'],
                         self._guest.guest_output_dir_path())
        self.change_file_permissions(
            self._guest.guest_output_dir_subpath('artifacts.tar.gz'))

    # TODO: this is a hack, should be fixed in artman instead
    #       (must be a way to configure output path)
    def _fix_generator_output(self):
        art_sub = ['artifacts', 'java']
        lr_dir = 'gapic-google-cloud-longrunning-v1'
        lr_path = self._guest.guest_output_dir_subpath(art_sub + [lr_dir])
        if os.path.exists(lr_path):
            new_lr_dir = 'gapic-google-longrunning-v1'
            cwd = self._guest.guest_output_dir_subpath(art_sub)
            self.run_command(['mv', lr_dir, new_lr_dir], cwd)


if __name__ == '__main__':
    execution_config = ConfigUtils.read_config()

    if 'execution_id' not in execution_config:
        execution_config['execution_id'] = ConfigUtils.generate_id(
            'java-src-stage-')

    step = SourcesGenerationGuest(execution_config)
    step.execute()
