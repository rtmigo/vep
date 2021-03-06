# SPDX-FileCopyrightText: (c) 2021 Artëm IG <github.com/rtmigo>
# SPDX-License-Identifier: BSD-3-Clause

import subprocess
import time
from subprocess import Popen, TimeoutExpired, CalledProcessError, \
    CompletedProcess, PIPE

from vien._common import need_posix


def run_as_bash_script(script: str, timeout: float = None,
                       input_delay: float = None,
                       capture_output: bool = False,
                       input: bytes = None,
                       **kwargs
                       ) -> subprocess.CompletedProcess:
    """Runs the provided string as a .sh script."""

    need_posix()

    # we need executable='/bin/bash' for Ubuntu 18.04, it will run '/bin/sh'
    # otherwise. For MacOS 10.13 it seems to be optional
    return _run_with_input_delay(script, shell=True, executable='/bin/bash',
                                 timeout=timeout,
                                 input=input,
                                 capture_output=capture_output,
                                 input_delay=input_delay,
                                 **kwargs)


def _run_with_input_delay(*popenargs, input_delay: float = None,
                          input=None, timeout: float = None,
                          check: bool = False,
                          capture_output: bool = False,
                          **kwargs):
    """Basically the same as subprocess.run, but accepts input_delay
    parameter."""

    # This is almost an exact copy of subprocess.run (as of 2021-03-06).
    # SPDX-FileCopyrightText: 2003-2005 Peter Astrand <astrand@lysator.liu.se>
    # https://github.com/python/cpython/blob/master/Lib/subprocess.py

    # START of insert from another portion of subprocess.py
    try:
        import msvcrt
        import _winapi
        _mswindows = True
    except ModuleNotFoundError:
        _mswindows = False
    # END of insert

    if input is not None:
        if kwargs.get('stdin') is not None:
            raise ValueError('stdin and input arguments may not both be used.')
        kwargs['stdin'] = PIPE

    if capture_output:
        if kwargs.get('stdout') is not None or kwargs.get('stderr') is not None:
            raise ValueError('stdout and stderr arguments may not be used '
                             'with capture_output.')
        kwargs['stdout'] = PIPE
        kwargs['stderr'] = PIPE

    with Popen(*popenargs, **kwargs) as process:
        try:
            # START of modified code
            if input is not None and input_delay:
                time.sleep(input_delay)
            # END of modified code

            stdout, stderr = process.communicate(input, timeout=timeout)
        except TimeoutExpired as exc:
            process.kill()
            if _mswindows:
                # Windows accumulates the output in a single blocking
                # read() call run on child threads, with the timeout
                # being done in a join() on those threads.  communicate()
                # _after_ kill() is required to collect that and add it
                # to the exception.
                exc.stdout, exc.stderr = process.communicate()
            else:
                # POSIX _communicate already populated the output so
                # far into the TimeoutExpired exception.
                process.wait()
            raise
        except:  # Including KeyboardInterrupt, communicate handled that.
            process.kill()
            # We don't call process.wait() as .__exit__ does that for us.
            raise

        exit_code = process.poll()

        # START of modified code
        if exit_code is None:
            raise RuntimeError("The process was not terminated.")
        # END of modified code

        if check and exit_code:
            raise CalledProcessError(exit_code, process.args,
                                     output=stdout, stderr=stderr)

    return CompletedProcess(process.args, exit_code, stdout, stderr)
