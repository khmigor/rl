# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.


import distutils.command.clean
import glob
import os
import shutil
import subprocess
from pathlib import Path

from setuptools import setup, find_packages
from torch.utils.cpp_extension import (
    CppExtension,
    BuildExtension,
)


def _get_pytorch_version():
    if "PYTORCH_VERSION" in os.environ:
        return f"torch=={os.environ['PYTORCH_VERSION']}"
    return "torch"


def _get_packages():
    exclude = [
        "build*",
        "test*",
        "torchrl.csrc*",
        "third_party*",
        "tools*",
    ]
    return find_packages(exclude=exclude)


ROOT_DIR = Path(__file__).parent.resolve()


class clean(distutils.command.clean.clean):
    def run(self):
        # Run default behavior first
        distutils.command.clean.clean.run(self)

        # Remove torchrl extension
        for path in (ROOT_DIR / "torchrl").glob("**/*.so"):
            print(f"removing '{path}'")
            path.unlink()
        # Remove build directory
        build_dirs = [
            ROOT_DIR / "build",
        ]
        for path in build_dirs:
            if path.exists():
                print(f"removing '{path}' (and everything under it)")
                shutil.rmtree(str(path), ignore_errors=True)


def _run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, cwd=ROOT_DIR).decode("ascii").strip()
    except Exception:
        return None


def get_extensions():
    extension = CppExtension

    extra_link_args = []
    extra_compile_args = {
        "cxx": [
            "-O3",
            "-std=c++14",
            "-fdiagnostics-color=always",
        ]
    }
    debug_mode = os.getenv("DEBUG", "0") == "1"
    if debug_mode:
        print("Compiling in debug mode")
        extra_compile_args = {
            "cxx": [
                "-O0",
                "-fno-inline",
                "-g",
                "-std=c++14",
                "-fdiagnostics-color=always",
            ]
        }
        extra_link_args = ["-O0", "-g"]

    this_dir = os.path.dirname(os.path.abspath(__file__))
    extensions_dir = os.path.join(this_dir, "torchrl", "csrc")

    extension_sources = set(
        os.path.join(extensions_dir, p)
        for p in glob.glob(os.path.join(extensions_dir, "*.cpp"))
    )
    sources = list(extension_sources)

    ext_modules = [
        extension(
            "torchrl._torchrl",
            sources,
            include_dirs=[this_dir],
            extra_compile_args=extra_compile_args,
            extra_link_args=extra_link_args,
        )
    ]

    return ext_modules


def _main():
    pytorch_package_dep = _get_pytorch_version()
    print("-- PyTorch dependency:", pytorch_package_dep)
    # branch = _run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    # tag = _run_cmd(["git", "describe", "--tags", "--exact-match", "@"])

    setup(
        name="torchrl",
        version="0.1",
        author="torchrl contributors",
        author_email="vmoens@fb.com",
        packages=find_packages(),
        ext_modules=get_extensions(),
        cmdclass={
            "build_ext": BuildExtension.with_options(no_python_abi_suffix=True),
            "clean": clean,
        },
        install_requires=[pytorch_package_dep, "numpy", "tensorboard", "packaging"],
        extras_require={
            "atari": ["gym", "atari-py", "ale-py", "gym[accept-rom-license]", "pygame"],
            "dm_control": ["dm_control"],
            "gym_continuous": ["mujoco-py", "mujoco"],
            "rendering": ["moviepy"],
            "tests": ["pytest", "pyyaml"],
            "utils": [
                "tqdm",
                "configargparse",
                "hydra-core>=1.1",
                "hydra-submitit-launcher",
            ],
        },
    )


if __name__ == "__main__":
    _main()
