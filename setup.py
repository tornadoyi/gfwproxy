# ----------------------------------------------------------------------------
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------------------------------------------------------
from os.path import dirname, join
from setuptools import setup, find_packages

# Define version information
NAME = 'gfwproxy'

# Define version information
with open(join(dirname(__file__), NAME + '/VERSION'), 'rb') as f:
      VERSION = f.read().decode('ascii').strip()




setup(
      name = 'gfwproxy',
      version = VERSION,
      description = "A tool dedicated for pass through chinese Great Fire Wall",
      author = 'yi gu',
      author_email = '390512308@qq.com',
      license = 'License :: OSI Approved :: Apache Software License',
      packages = find_packages(),
      include_package_data=True,
      zip_safe = False,
      install_requires = [
            'argparse',
            'pyplus',
            'genpac',
            'shadowsocks'
      ],
      dependency_links=['git+https://github.com/tornadoyi/pyplus.git@r0.1#egg=pyplus'],

      entry_points = {
            'console_scripts': [
                  'gfwproxy = gfwproxy.cli:main',
              ],
      },
)