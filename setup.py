from setuptools import setup
import os 
from collections import OrderedDict

try:
    long_description = ""
    with open('README.md', encoding='utf-8') as f:
        long_description = f.read()

except:
    print('Curr dir:', os.getcwd())
    long_description = open('../../README.md').read()

setup(name='dblpconf',
      version='0.0.4',
      description='dblp conf',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/WolfgangFahl/dblpconf',
      download_url='https://github.com/WolfgangFahl/dblpconf',
      author='Wolfgang Fahl',
      author_email='wf@bitplan.com',
      license='Apache',
      project_urls=OrderedDict(
        (
            ("Documentation", "http://wiki.bitplan.com/index.php/Dblpconf"),
            ("Code", "https://github.com/WolfgangFahl/dblpconf"),
            ("Issue tracker", "https://github.com/WolfgangFahl/dblpconf/issues"),
        )
      ),
      classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9'
      ],
      packages=['dblp'],
      package_data={
          'templates': ['*.html'],
      },
      install_requires=[
        'pyFlaskBootstrap4',
        'py-3rdparty-mediawiki>=0.1.23',
        'pylodstorage',
        'lxml',
        'OpenResearchMigration>=0.0.3',
        'wikirender>=0.0.5'
      ],
      zip_safe=False)
