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
import tempfile
import uuid
import os
import subprocess
import sys
from ruamel import yaml


class ConfigUtils(object):
    def __init__(self):
        pass

    @staticmethod
    def read_config(yaml_file_path=None, yaml_str=None, execution_id=None):
        config = ConfigUtils._read_config(yaml_file_path, yaml_str)
        if ('execution_id' not in config) and execution_id:
            config['execution_id'] = execution_id
        return config

    @staticmethod
    def _read_config(yaml_file_path=None, yaml_str=None):
        if yaml_str:
            return yaml.safe_load(yaml_str)
        elif yaml_file_path:
            with open(yaml_file_path) as config_file:
                return yaml.safe_load(config_file.read())
        elif len(sys.argv) <= 1:
            return yaml.safe_load(sys.stdin)
        else:
            with open(sys.argv[1]) as config_file:
                return yaml.safe_load(config_file.read())

    @staticmethod
    def dump_config(config, output):
        if isinstance(output, str):
            with open(output, 'w') as config_file:
                yaml.round_trip_dump(config, config_file)
        else:
            yaml.round_trip_dump(config, output)
            output.flush()

    @staticmethod
    def generate_id(prefix):
        return "%s%s" % (prefix, str(uuid.uuid4())[24:])

    @staticmethod
    def artifact_name():
        return 'artifacts.tar.gz'

    @staticmethod
    def artifact_yaml_name():
        return 'artifacts.yaml'

    @staticmethod
    def check_artifact_exist(step_props, artifact_name):
        artifacts_fl = step_props.host_guest_output_dir_subpath(artifact_name)
        return os.path.isfile(artifacts_fl)


class GitUtils(object):
    def __init__(self):
        pass

    @staticmethod
    def clone_command(config, branch=None):
        actual_branch = branch
        if not actual_branch:
            actual_branch = config['git_branch']

        repo = config['git_repo']
        repo_owner, repo_name = GitUtils.repo_properties(repo)
        if 'git_user_name' in config and 'git_security_token' in config:
            repo_tokens = re.compile(r'(://+)').split(repo)
            creds = "%s:%s@" % (
                config['git_user_name'], config['git_security_token'])
            repo_tokens.insert(2, creds)
            repo = ''.join(repo_tokens)

        return ['git', 'clone', repo, '--branch', actual_branch,
                '--single-branch', repo_name]

    @staticmethod
    def repo_properties(repo_url):
        if repo_url.startswith('/'):
            return None, repo_url[repo_url.rfind('/'):]

        repo_owner, repo_name = repo_url.split('/')[-2:]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]

        return repo_owner, repo_name


class HostStepProperties(object):
    _EXECUTION_ID_PATTERN = re.compile(r'^[\w\-.]+$')

    def __init__(self, script_file_path, execution_id):
        self._script_file_path = script_file_path
        self._execution_id = execution_id
        if not self._EXECUTION_ID_PATTERN.match(execution_id):
            raise ValueError('Invalid execution id')

    def execution_id(self):
        return self._execution_id

    def step_name(self):
        script_file_basename = os.path.basename(self._script_file_path)
        return script_file_basename[:script_file_basename.rindex('_')]

    def step_dir_path(self):
        return os.path.dirname(os.path.realpath(self._script_file_path))

    def temp_path(self):
        return os.path.join(tempfile.gettempdir(),
                            'artmanflow-' + self.execution_id())

    def temp_subpath(self, basename):
        return os.path.join(self.temp_path(), basename)

    def stdout_file_path(self):
        return os.path.join(self.temp_path(), self.step_name() + '-stdout')

    def host_guest_config_file_path(self):
        return os.path.join(self.temp_path(),
                            self.step_name() + '_guest.yaml')

    def host_guest_output_dir_path(self):
        return os.path.join(self.temp_path(), 'guest_output')

    def host_guest_output_dir_subpath(self, basename):
        return os.path.join(self.host_guest_output_dir_path(), basename)

    def guest_script_name(self):
        return self.step_name() + '_guest.py'


class GuestStepProperties(object):
    def __init__(self, guest_root_path):
        self._guest_root_path = guest_root_path

    def guest_root_path(self):
        return self._guest_root_path

    def guest_root_subpath(self, basename):
        paths = [self.guest_root_path()]
        paths.extend(basename if isinstance(basename, list) else [basename])
        return '/'.join(paths)

    def guest_step_dir_path(self):
        return '/'.join([self.guest_root_path(), 'steps'])

    def guest_output_dir_path(self):
        # return self.guest_root_path()
        return '/'.join([self.guest_root_path(), 'guest_output'])

    def guest_root_dir_snapshot_path(self):
        return '/'.join(
            [self.guest_output_dir_path(), 'guest_root_dir_snapshot'])

    def guest_output_dir_subpath(self, basename):
        paths = [self.guest_output_dir_path()]
        paths.extend(basename if isinstance(basename, list) else [basename])
        return '/'.join(paths)

    def guest_client_yaml_file_path(self, relative_path):
        return '/'.join([self.guest_root_path(), relative_path])

    def guest_script_path(self, guest_script_name):
        return '/'.join([self.guest_step_dir_path(), guest_script_name])

    def relative_path(self, basenames):
        return '/'.join(basenames)


class BaseHost(object):
    def __init__(self, host_step_properties, config):
        self._config = config
        self._host = host_step_properties
        self._guest = GuestStepProperties(config['guest_root_path'])

    def pre_execute(self):
        try:
            os.makedirs(self._host.temp_path())
        except OSError:
            pass  # assume dir already exists
        with open(self._host.stdout_file_path(), 'a'):
            pass

    def run_guest_script(self, guest_config, extra_mount_volumes=None):
        host_guest_config_file_path = self._host.host_guest_config_file_path()
        ConfigUtils.dump_config(guest_config, host_guest_config_file_path)

        host_guest_output_dir = self._host.host_guest_output_dir_path()
        os.makedirs(host_guest_output_dir)

        mount_volumes = [
            [self._host.step_dir_path(), self._guest.guest_step_dir_path(),
             'ro'],
            [host_guest_output_dir, self._guest.guest_output_dir_path()],
        ]

        if extra_mount_volumes:
            mount_volumes.extend(extra_mount_volumes)

        script_path = self._guest.guest_script_path(
            self._host.guest_script_name())
        self._run_command(['python3', script_path],
                          host_guest_config_file_path,
                          self._host.stdout_file_path(),
                          self._guest.guest_root_path(),
                          mount_volumes)

    def _run_command(self, command, input_file_name, output_file_name,
        guest_root_path=None, mount_dirs=None):

        cmd = self._construct_docker_run_command(command, guest_root_path,
                                                 mount_dirs)
        with open(input_file_name, 'r') as input_file, \
            open(output_file_name, 'a+') as output_file:
            output_file.write(
                "\033[1;30msubprocess.Popen(%s, stdout='%s', stderr='%s', stdin='%s'\n\033[0m\n" % (
                    cmd, output_file_name, output_file_name, input_file_name))
            output_file.flush()
            subprocess.Popen(cmd, stdout=output_file, stderr=output_file,
                             stdin=input_file)

    def _construct_docker_run_command(self, command, guest_root_path=None,
        mount_dirs=None):
        cmd = ['docker', 'run', '--rm']  # run and remove container after exit
        if guest_root_path:
            cmd += ['-w', guest_root_path]  # set working dir
        if mount_dirs:
            for mount_dirs_pair in mount_dirs:
                cmd += ['-v', ':'.join(mount_dirs_pair)]  # mount volumes
        cmd += [
            '-e', 'HOST_USER_ID=%s' % os.getuid(),  # to chown inside  docker
            '-e', 'HOST_GROUP_ID=%s' % os.getgid(),
            '-i', self._config['docker_image']  # specify image
        ]
        cmd += command

        return cmd

    def local_repo_mount(self, config):
        repo = config['git_repo']
        if repo.startswith('file://'):
            local_mount_path = repo[len('file://'):]
        elif repo.startswith('/'):
            local_mount_path = repo
        else:
            return []

        local_repo_name = local_mount_path[local_mount_path.rfind('/') + 1:]
        guest_mount_path = self._guest.guest_root_subpath(local_repo_name)

        return [local_mount_path, guest_mount_path]


class BaseGuest(object):
    def __init__(self, config):
        self._config = config
        self._guest = GuestStepProperties(config['guest_root_path'])

    def before_execute(self):
        self.puts(">>>>>>>>>> START GUEST SCRIPT EXECUTION: %s\n" % ' '.join(
            sys.argv))
        self.puts('Guest Script config:\n', '\033[1;30m', '\033[36m')
        ConfigUtils.dump_config(self._config, sys.stdout)
        self.puts(end_color='\033[0m')

    def after_execute(self, save_guest_files_snapshot, exception=None):
        snapshot_path = self._guest.guest_root_dir_snapshot_path()
        if exception:
            self.puts(
                "Exception was thrown: %s. Saving guest script root"
                " directory snapshot for debugging at: %s" % (
                    str(exception), snapshot_path))
        if exception or save_guest_files_snapshot:
            self._create_guest_files_snapshot(snapshot_path)
        self.puts("<<<<<<<<< END GUEST SCRIPT EXECUTION")

    def puts(self, message='', start_color="\033[1;30m", end_color='\033[0m'):
        sys.stdout.flush()
        print("%s%s%s" % (start_color, message, end_color))
        sys.stdout.flush()

    def run_command(self, command, cwd=None, hide_command=False):
        print_command = '*****' if hide_command else command
        self.puts(
            "\033[1;30msubprocess.check_call(%s, cwd='%s')\033[0m" % (
                print_command, cwd))
        subprocess.check_call(command, cwd=cwd)
        sys.stdout.flush()

    def check_command(self, command, cwd=None, hide_command=False):
        print_command = '*****' if hide_command else command
        self.puts(
            "\033[1;30msubprocess.check_output(%s, cwd='%s')\033[0m" % (
                print_command, cwd))
        rv = subprocess.check_output(command, cwd=cwd)
        sys.stdout.flush()
        return rv

    def change_file_permissions(self, path):
        user_host_id = int(os.getenv('HOST_USER_ID', 0))
        group_host_id = int(os.getenv('HOST_GROUP_ID', 0))
        if user_host_id and group_host_id:
            user_and_group = "%s:%s" % (user_host_id, group_host_id)
            self.run_command(['chown', '-R', user_and_group, path],
                             hide_command=False)

    def _create_guest_files_snapshot(self, snapshot_path):
        output_path = self._guest.guest_output_dir_path()
        # snapshot_path = self._guest.guest_root_dir_snapshot_path()

        self.run_command(['mkdir', '-p', snapshot_path])
        for root, sub_dirs, files in os.walk(self._guest.guest_root_path()):
            for sub_dir in sub_dirs:
                sub_dir_path = self._guest.guest_root_subpath(sub_dir)
                if sub_dir_path == output_path:
                    continue
                self.run_command(
                    ['cp', '-R', sub_dir_path, snapshot_path])
            for file in files:
                file_path = self._guest.guest_root_subpath(file)
                self.run_command(
                    ['cp', file_path, snapshot_path])
            break

        self.change_file_permissions(snapshot_path)

    def checkout_git_input_repo(self, config):
        # Do not checkout if locally mounted.
        # Assume the repo is already in a desired state (commit, branch, etc).
        if config['git_repo'].startswith('/'):
            repo_owner, repo_name = GitUtils.repo_properties(config['git_repo'])
            return repo_name

        command = GitUtils.clone_command(config)
        self.run_command(command, self._guest.guest_root_path())
        git_repo_path = self._guest.guest_root_subpath(command[-1])
        self.run_command(
            ['git', 'checkout', config['git_commit']], cwd=git_repo_path)
        self.change_file_permissions(git_repo_path)
        return command[-1]

    def checkout_git_output_repo(self, config):
        git_cmd = GitUtils.clone_command(config, 'master')
        self.run_command(git_cmd, self._guest.guest_root_path(), True)
        git_repo_path = self._guest.guest_root_subpath(git_cmd[-1])
        self.run_command(
            ['git', 'checkout', '-b', config['git_branch']], git_repo_path)

        self.change_file_permissions(git_repo_path)
        return git_cmd[-1]
