# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause


import argparse
import datetime as dt

from svet import __version__
from svet.bashAliasRunner import runWithBashAliases

venvsRoot = "~/.pyvnv/"

__doc__ = f"""
# 

VEP helps managing virtual environments located in {venvsRoot} 

For a Python project /path/to/myProject/ virtualenv will be located in 
in {venvsRoot}myProject_venv/

To CREATE new virtualenv with Python 3.8 in {venvsRoot}myProject_venv/:

	cd /path/to/myProject
	vep init 3.8
	
To REMOVE old and CREATE new virtualenv:

	cd /path/to/myProject
	vep reinit 3.8
 		
To RUN a PYTHON SCRIPT inside "myProject_venv" environment:	

	cd /path/to/myProject
	vep run python ./myProgram.py
	
To RUN a BASH SUBSHELL inside "myProject_venv" environment:	

	cd /path/to/myProject
	vep shell

"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import *

verbose = False

import unittest


def getVepsDir() -> Path:
	s = os.environ.get("VEPDIR")
	if s:
		return Path(os.path.expanduser(os.path.expandvars(s)))
	else:
		return Path(os.path.expandvars("$HOME")) / ".vepvep"


class TestVenvsDir(unittest.TestCase):

	def test_if_set_plain(self):
		os.environ["VEPDIR"] = "/path/to/veps"
		self.assertEqual(getVepsDir(), Path('/path/to/veps'))

	def test_if_set_with_vars(self):
		os.environ["VEPDIR"] = "$HOME/subfolder"
		s = str(getVepsDir())
		self.assertTrue("$" not in s)
		self.assertGreater(len(s), len("/home/"))

	def test_if_set_with_user(self):
		os.environ["VEPDIR"] = "~/subfolder"
		s = str(getVepsDir())
		self.assertTrue("~" not in s)
		self.assertGreater(len(s), len("/home/"))

	def test_if_not_n(self):
		if "VEPDIR" in os.environ:
			del os.environ["VEPDIR"]
		p = str(getVepsDir())
		self.assertTrue(p.endswith("vepvep"))
		self.assertGreater(len(p), len("/.vepvep"))


def run(args: List[str]):
	if verbose:
		print(f"Running {args}")
	subprocess.run(args, shell=True)


def runseq(commands: List[str]):
	joined = ' && '.join(commands)
	if verbose:
		print(f"Running '{joined}'")
	return os.system(joined)


def quote(arg: str) -> str:
	return json.dumps(arg)


def venvDirToExe(venvDir: Path) -> Path:
	return venvDir / "bin" / "python"


def init(venvDir: Path, version: str):
	if venvDir.exists():
		raise Exception("Venv already exists.")

	exe = version

	print(f"Creating {venvDir}")

	runWithBashAliases(f'{exe} -m venv "{str(venvDir)}"')

	print()
	print("Configure PyCharm with Python executable:")
	print(str(venvDirToExe(venvDir)))


def reinit(venvDir: Path, version: str):
	if not "_venv" in venvDir.name:
		raise Exception
	if venvDir.exists():
		print(f"Removing {venvDir}")
		shutil.rmtree(str(venvDir))
	init(venvDir=venvDir, version=version)


def shell(venvDir: Path, venvName: str):
	useColor = True
	YELLOW = "\e[33m"
	CYAN = r"\e[36m"
	NOCOLOR = r"\e[0m"  #

	activatePathQuoted = quote(str(venvDir / "bin" / "activate"))

	if useColor:
		ps = f"\\[{CYAN}vep@{venvName}> {NOCOLOR}\\]"  # fancy but buggy
	else:
		ps = f"vep@{venvName}> "

	commands = [
		f'source {activatePathQuoted}',
		f'export PS1="{ps}"',
		'exec bash'
	]

	exit(runseq(commands))


def runargs(venvDir: Path, otherargs):
	commands = [
		f'source "{venvDir}/bin/activate"',
		" ".join(quote(a) for a in otherargs)
	]

	exit(runseq(commands))


def version() -> str:
	modTimestamp = (Path(__file__).parent / "constants.py").stat().st_mtime
	modYear = dt.datetime.fromtimestamp(modTimestamp).year
	return "\n".join([
		f"SVET: Simple Virtual Environments Tool {__version__}",
		f"(c) 2020-{modYear} Art Galkin <ortemeo@gmail.com>",
		f"See https://github.com/rtmigo/svet#readme"
	])


# print(f"SVET {__version__} : (c) 2020-{y} Art Galkin <ortemeo@gmail.com>")
# print(f"https://github.com/rtmigo/vep#readme")


class RawFormatter(argparse.HelpFormatter):
	"""Allows no use newline characters in ArgumentParser description.
	Unlike argparse.RawTextHelpFormatter wraps long lines to fit width."""

	def _fill_text(self, text, width, indent):
		import textwrap

		# to make the use of indented docstrings more convenient
		text = "\n".join([line.strip() for line in text.splitlines()])

		# https://stackoverflow.com/a/64102901
		return "\n".join([
			textwrap.fill(line, width)
			for line in textwrap.indent(textwrap.dedent(text), indent).splitlines()])


def runmain():
	# noinspection PyTypeChecker
	parser = argparse.ArgumentParser(
		description=f"""
		SVET: Simple Virtual Environments Tool""",
		formatter_class=RawFormatter
	)

	subparsers = parser.add_subparsers(dest='command', required=True)

	parser_init = subparsers.add_parser('init', help="create new virtualenv")
	parser_init.add_argument('python', type=str)

	parser_reinit = subparsers.add_parser('reinit',
										  help="remove existing virtualenv and create new")
	parser_reinit.add_argument('python', type=str)

	subparsers.add_parser('shell', help="dive into Bash subshell using the virtualenv")

	parser_run = subparsers.add_parser('run', help="run a command inside the virtualenv")
	parser_run.add_argument('otherargs', nargs='*')

	subparsers.add_parser('path',
						  help="show the supposed path of the virtualenv for the current directory")

	parser.add_argument('-v', '--version',  # action="store_true",
						action='version',
						version=version())

	args = parser.parse_args()

	###########

	projectDir = Path(".").absolute()
	venvDir = getVepsDir() / (
			projectDir.name + "_venv")  # venvsParentDir / (projectDir.name + "_venv")

	if verbose:
		print(f"Proj dir: {projectDir}")
		print(f"Venv dir: {venvDir}")

	##########

	#	if args.version:
	#		ver()
	#		exit(0)
	if args.command == "init":
		init(venvDir, args.python)
	elif args.command == "reinit":
		reinit(venvDir, args.python)
	elif args.command == "path":
		print(venvDir)
	elif args.command == "run":
		runargs(venvDir, args.otherargs)
	elif args.command == "shell":
		shell(venvDir, projectDir.name)
	else:
		raise ValueError
