# -*- coding:utf-8 -*-
"""
filename : setup.py
createtime : 2021/2/8 21:43
author : Demon Finch
"""
from setuptools import setup, Command
import os
import shutil

whl_name = 'tick_down'


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    @staticmethod
    def run():
        shutil.rmtree(os.path.join(os.path.dirname(__file__), f"{whl_name}.egg-info"))
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "build"))
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "dist"))


def get_version():
    ret = os.popen(f"pip list |grep {whl_name[:4]} | grep {whl_name[-4:]}").read()
    if len(ret) > 1:
        return round(float(ret.split(" ")[-1].strip()) + 0.1, 1)
    else:
        return 0.1


setup(name=whl_name,
      version=get_version(),
      description=whl_name,
      author='yhf2lj',
      author_email='yhf2lj@gmail.com',
      url='',
      packages=[whl_name],
      install_requires=["requests", "akshare", 'func_timeout'],
      license="MIT",
      cmdclass={
          'clean': CleanCommand,
      }
      )
