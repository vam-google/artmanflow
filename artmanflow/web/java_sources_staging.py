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
    render_template, request, redirect

from artmanflow.steps.java_sources_staging_host import JavaSourcesStagingHost
from artmanflow.steps.common import ConfigUtils
from artmanflow.web.html_utils import HtmlUtils
from artmanflow.web.service_utils import ServiceUtils

java_src_staging = Blueprint('java_sources_staging', __name__,
                             url_prefix='/java-sources-staging')


@java_src_staging.route('/new')
def java_sources_staging_new():
    config = _params_from_yaml(
        ServiceUtils.get_step_default_config('java_sources_staging.yaml'))
    return render_template('java_sources_staging_new.html', config=config)


@java_src_staging.route('', methods=['POST'])
def java_sources_staging():
    step_props = JavaSourcesStagingHost.host_step_properties(
        ConfigUtils.generate_id('java-src-stage-'))

    config_yaml = ServiceUtils.get_step_config(request.form,
                                               'java_sources_staging.yaml',
                                               _params_to_yaml)
    artifacts_zip_path = step_props.temp_subpath(ConfigUtils.artifact_name())
    config_yaml['generator_artifacts']['sources_zip'] = artifacts_zip_path
    execution_id = step_props.execution_id()
    config_yaml['staging']['git_branch'] = execution_id
    config_yaml['execution_id'] = execution_id

    ServiceUtils.run_host_step(JavaSourcesStagingHost(config_yaml))

    step = JavaSourcesStagingHost(config_yaml)
    step.pre_execute()
    request.files['generator_artifacts_sources_zip'].save(artifacts_zip_path)
    ServiceUtils.run_host_step(step)

    return redirect("/java-sources-staging/%s" % step_props.execution_id())


@java_src_staging.route('/<execution_id>')
def java_sources_staging_output(execution_id):
    step_props = JavaSourcesStagingHost.host_step_properties(execution_id)
    artifact_name = ConfigUtils.artifact_yaml_name()
    pr_url = None

    if ConfigUtils.check_artifact_exist(step_props, artifact_name):
        artifact = ConfigUtils.read_config(
            step_props.host_guest_output_dir_subpath(
                ConfigUtils.artifact_yaml_name()))
        pr_url = artifact['pr_url']

    rows = HtmlUtils.generate_html_from_console_output(
        step_props.stdout_file_path())
    stream = ServiceUtils.stream_template('java_sources_staging_output.html',
                                          rows=rows, pr_url=pr_url,
                                          output_link=step_props.temp_path())
    return Response(stream, mimetype='text/html')


def _params_to_yaml(post_params, extra_config):
    config = {
        'docker_image': post_params['docker_image'],
        'debug_mode': True if 'debug_mode' in post_params else False,
        'staging': {
            'git_user_name': post_params['staging_git_user_name'],
            'git_security_token': post_params['staging_git_security_token'],
            'git_repo': post_params['staging_git_repo'],
            'run_tests': True if 'staging_run_tests' in post_params else False
        },
        'generator_artifacts': {}
    }
    config.update(extra_config)

    return config


def _params_from_yaml(yaml_params):
    config = {
        'docker_image': yaml_params['docker_image'],
        'debug_mode': str(yaml_params['debug_mode']),
        'staging_git_user_name': yaml_params['staging']['git_user_name'],
        'staging_git_security_token': yaml_params['staging'][
            'git_security_token'],
        'staging_git_repo': yaml_params['staging']['git_repo'],
        'staging_run_tests': str(yaml_params['staging']['run_tests'])
    }
    return config
