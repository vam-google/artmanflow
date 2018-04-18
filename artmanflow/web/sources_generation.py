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

from flask import Blueprint, Response, \
    render_template, request, redirect, send_from_directory

from artmanflow.steps.sources_generation_host import SourcesGenerationHost
from artmanflow.steps.common import ConfigUtils
from artmanflow.web.html_utils import HtmlUtils
from artmanflow.web.service_utils import ServiceUtils

src_gen = Blueprint('sources_generation', __name__,
                    url_prefix='/sources-generation')


@src_gen.route('/new')
def sources_generation_new():
    config = _params_from_yaml(
        ServiceUtils.get_step_default_config('sources_generation.yaml'))
    return render_template('sources_generation_new.html', config=config)


@src_gen.route('', methods=['POST'])
def sources_generation():
    config_yaml = ServiceUtils.get_step_config(request.form,
                                               'sources_generation.yaml',
                                               _params_to_yaml)

    execution_id = ConfigUtils.generate_id('src-gen-')
    config_yaml['execution_id'] = execution_id
    step = SourcesGenerationHost(config_yaml)
    ServiceUtils.run_host_step(step)

    return redirect("/sources-generation/%s" % execution_id)


@src_gen.route('/<execution_id>')
def sources_generation_output(execution_id):
    step_props = SourcesGenerationHost.host_step_properties(execution_id)
    artifact_name = ConfigUtils.artifact_name()
    download_link = None
    if ConfigUtils.check_artifact_exist(step_props, artifact_name):
        download_link = "/sources-generation/%s/download" % execution_id

    rows = HtmlUtils.generate_html_from_console_output(
        step_props.stdout_file_path())

    output_path = step_props.temp_path()
    stream = ServiceUtils.stream_template('sources_generation_output.html',
                                          rows=rows,
                                          download_link=download_link,
                                          output_link=output_path)
    return Response(stream, mimetype='text/html')


@src_gen.route('/<execution_id>/download')
def sources_generation_download(execution_id):
    step_props = SourcesGenerationHost.host_step_properties(execution_id)
    artifact_name = ConfigUtils.artifact_name()

    if ConfigUtils.check_artifact_exist(step_props, artifact_name):
        return send_from_directory(step_props.host_guest_output_dir_path(),
                                   artifact_name, as_attachment=True,
                                   attachment_filename=artifact_name,
                                   mimetype='application/gzip')
    else:
        return 'The artifact does not exist. Please ensure that the provided ' \
               'execution_id is correct and the generation phase is finished ' \
               'and try again', 404


def _params_to_yaml(post_params, extra_config):
    yaml_configs_list = post_params[
        'artman_client_yaml_configs'].splitlines()
    converted_yaml_configs = []

    for client_yaml_config in yaml_configs_list:
        parts = client_yaml_config.strip().partition(':')
        converted_yaml_configs.append(
            {'path': parts[0], 'target': parts[2]})

    config = {
        'docker_image': post_params['docker_image'],
        'local_volumes': post_params.get('local_volumes', ''),
        'debug_mode': True if 'debug_mode' in post_params else False,
        'artman': {
            'git_repo': post_params['artman_git_repo'],
            'git_branch': post_params['artman_git_branch'],
            'git_commit': post_params['artman_git_commit']
        },
        'toolkit': {
            'git_repo': post_params['toolkit_git_repo'],
            'git_branch': post_params['toolkit_git_branch'],
            'git_commit': post_params['toolkit_git_commit']
        },
        'googleapis': {
            'git_repo': post_params['googleapis_git_repo'],
            'git_branch': post_params['googleapis_git_branch'],
            'git_commit': post_params['googleapis_git_commit']
        },
        'artman_client_yaml_configs': converted_yaml_configs
    }
    config.update(extra_config)

    return config


def _params_from_yaml(yaml_params):
    yaml_configs_list = yaml_params['artman_client_yaml_configs']
    converted_yaml_config = []
    for entry in yaml_configs_list:
        converted_yaml_config.append(
            "%s:%s" % (entry['path'], entry['target']))

    config = {
        'docker_image': yaml_params['docker_image'],
        'local_volumes': yaml_params['local_volumes'],
        'debug_mode': str(yaml_params['debug_mode']),
        'artman_git_repo': yaml_params['artman']['git_repo'],
        'artman_git_branch': yaml_params['artman']['git_branch'],
        'artman_git_commit': yaml_params['artman']['git_commit'],
        'toolkit_git_repo': yaml_params['toolkit']['git_repo'],
        'toolkit_git_branch': yaml_params['toolkit']['git_branch'],
        'toolkit_git_commit': yaml_params['toolkit']['git_commit'],
        'googleapis_git_repo': yaml_params['googleapis']['git_repo'],
        'googleapis_git_branch': yaml_params['googleapis']['git_branch'],
        'googleapis_git_commit': yaml_params['googleapis']['git_commit'],
        'artman_client_yaml_configs': '\n'.join(converted_yaml_config)
    }
    return config


def _check_artifacts_exist(step_props):
    artifacts_fl = step_props.host_guest_output_dir_subpath(
        ConfigUtils.artifact_name())
    return os.path.isfile(artifacts_fl)

# def _get_default_config(config_file_name):
#     default_generation_config_str = render_template(config_file_name)
#     default_generation_config_yaml = ConfigUtils.read_config(
#         default_generation_config_str)
#     return default_generation_config_yaml
