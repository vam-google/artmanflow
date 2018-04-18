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
from flask import Flask, render_template

from artmanflow.web.sources_generation import src_gen
from artmanflow.web.java_sources_staging import java_src_staging

app = Flask(__name__)

# Step 1: Generate Sources
app.register_blueprint(src_gen)

# Step 2: Generate Keys

# Step 3: Stage Sources
app.register_blueprint(java_src_staging)


# Step 4: Stage Dependencies Artifacts

# Step 5: Release Sources

# Step 6: Stage Artifacts

@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
