from setuptools import setup, find_packages
import os

version = '2.0a1'

setup(name='wc.pageturner',
      version=version,
      description="A Plone product that provides the PDF viewer FlexPaper.",
      long_description='%s\n\n%s\n\n%s' % (
          open("README.txt").read(),
          open(os.path.join("docs", "HISTORY.txt")).read(),
          open(os.path.join("docs", "ROADMAP.txt")).read()
      ),
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Framework :: Plone",
          "Programming Language :: Python",
      ],
      keywords='plone pdf flexpaper flex paper scridb',
      author='Nathan Van Gheem',
      author_email='vangheem@gmail.com',
      url='https://github.com/collective/wc.pageturner',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['wc'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'plone.app.contenttypes'
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """
      )
