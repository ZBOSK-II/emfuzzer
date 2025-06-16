Emfuzzer  
_fuzzing experiments orchestrator for embedded systems_
============================================================

When executing fuzzing experiment on embedded environment
one often faces challenge of performing multiple tasks in
reapetable and observable manner, for example: reset board,
ensure embedded software booted, send fuzzing data using
selected link, monitor peripheral state to detect changes
in behaviour etc.

This is what Emfuzzer helps to orchestrate: it runs various
tools and scripts in specific manner, then gathers their
results for further inspections.

_Note_: although focused on fuzzing and embedded systems,
Emfuzzer can help with any software-related experiments,
that require repeatable order of tasks and results capture.


Installation
------------------------------------------------------------
Emfuzzer is available on PyPI, it is recommended to install
it in isolated environment, either by using Python `venv` or
tools like `pipx`.

``` shell
python -m venv .venv
source .venv/bin/activate
pip install emfuzzer
```

``` shell
pipx install emfuzzer
```

Usage
------------------------------------------------------------
To run experiments simply run:

``` shell
emfuzzer --config=experiment.json test1.bin test2.bin
```

For each specified data file steps from `experiment.json`
will be executed and gathered results stored in file named
`emfuzzer-CURRENTDATE.json`. Application will output logs
to the console and also store them in `.log` file next to
the `.json` results file. The prefix for output files can
be modified using `--output-prefix` command line switch.

See `default-config.json` in source directory for example
of experiment definition (this file can be safely used -
the "experiment" calls `cat` on each passed file).

To obtain complete command line switches documentation call
`emfuzzer --help`.


Experiment
------------------------------------------------------------
Each data file passed to the emfuzzer represents a single
Test Case. For each test case following experiment steps
will be performed:

 1. Setup tasks will be executed and their results stored.
 2. Monitoring tasks will be started.
 3. Injector will use Test Case data to perform the main
    experiment task (e.g. fuzzing data injection).
 4. Injector will observe system behaviour to capture
    result of the injection.
 5. Monitoring tasks will finish, their results stored.
 6. Check tasks will be executed and their results stored.
 7. Go to 1 for next Test Case.

Configuration
------------------------------------------------------------
Experiment configuration is stored in JSON format.

See chapters below for list of all types of injectors, tasks
and monitors (with arguments).

Below is the `default-config.json` with comments:
``` json-with-comments
{
  "delays": {
    "between_cases": 0.2, // delay between Test Cases
    "before_inject": 1    // delay after all setups
  },
  "injector": {
    "type": "subprocess", // type of injection
    "args": {             // arguments for given injector
      "cmd": [
        "cat"
      ],
      "shell": false,
      "timeout": 1
    }
  },
  "case": {                    // for each case
    "setups": [                // list of setups
      {
        "type": "subprocess",  // type of setup tasks
        "name": "setup",       // name used in results
        "args": {              // arguments for given setup
          "cmd": [
            "echo",
            "SETUP"
          ],
          "finish": {
            "timeout": 0.5,
            "signal": "NONE"
          },
          "shell": false
        }
      },
      {                        // second setup
        "type": "ping_alive",
        "name": "ping",
        "args": {
          "host": "127.0.0.1",
          "timeout": 10,
          "interval": 1
        }
      }
    ],
    "monitoring": [],          // monitoring tasks
    "checks": [                // list of checks tasks
      {                        // same as setups
        "type": "ping_stable",
        "name": "ping",
        "args": {
          "host": "127.0.0.1",
          "count": 2,
          "interval": 1
        }
      },
      {
        "type": "subprocess",
        "name": "teardown",
        "args": {
          "cmd": [
            "echo",
            "TEARDOWN"
          ],
          "finish": {
            "timeout": 0.5,
            "signal": "NONE"
          },
          "shell": false
        }
      }
    ]
  }
}
```


Injectors
------------------------------------------------------------
Injectors are the tools that take the experiment data,
use it to "inject" it into the system, and then observe the
effects. Currently supported injectors' types:

 * `subprocess` - execute script and captures its exit code.
   Arguments:
    - `cmd` - (list of strings) command to be executed, data
      will be passed as the last argument to the call
    - `shell` - (boolean) true when shell should be used todo
      interpret the command
    - `timeout` - (float) time to wait for command to finish
 * `coap` - CoAP (Constrained Application Protocol) injector
   data will be sent over UDP to specified address, success
   when positive response is received from the system.
   Arguments:
    - `target` - dictionary containing `host` and `port` of
      the target
    - `response_timeout` - (float) timeout to wait for CoAP
      response after sending the data
    - `observation_timeout` - (float) additional time for
      detecting any unexpected messages _after_ the response

SubTasks & Monitors
------------------------------------------------------------
Sub Tasks are tasks that for each case can be executed as
setups or checks.

_Note_: failure of "setup" _does not_ interrupt the test
case execution - it is logged and stored in results, next
steps are still executed, to be analyzed later.

Monitors are tasks that their execution is started after
setups, then they are active during the injection and
finish before checks.

Available tasks:
 * `subprocess` - execute script and capture its exit code.
   Arguments:
    - `cmd` - (list of strings) command to be executed
    - `shell` - (boolean) true when shell should be used todo
      interpret the command
    - `finish` - configuration of finishing the task:
      - `signal` - (string) signal name to be sent to the
        task (can be `NONE`)
      - `timeout` - (float) time to wait for command to
        finish (starts after signal is sent)
 * `ping_stable` - pings a target number of times, expects
   all pings to reply.
   Arguments:
     - `host` - (string) host to be checked
     - `count` - (integer) number of pings to sent
     - `interval` - (integer) interval between pings
 * `ping_alive` - pings a target and expects first response
   Arguments:
     - `host` - (string) host to be checked
     - `timeout` - (float) timeout to wait for response
     - `interval` - (integer) interval between pings
 * `remote` - executes command over SSH and captures its
   exit code.
   Arguments:
     - `connection` - dictionary containing:
       - `host`
       - `port`
       - `username`
       - `password`
     - `command` - (string) command to be executed
     - `start_key` - (string) string expected in the output
       of the executed command for the command to be considered
       "started successfully"
     - `start_timeout` - (float) timeout for the start of
       the command
    - `finish` - configuration of finishing the task:
      - `signal` - (string) signal name to be sent to the
        task (can be `NONE`)
      - `timeout` - (float) time to wait for command to
        finish (starts after signal is sent)
 * `coap_monitor` - listens for CoAP responses
   Arguments:
    - `target` - dictionary containing `host` and `port` of
      the target
    - `response_timeout` - (float) timeout to wait for CoAP
      response after sending any data
      (useful only when used as Injector)
    - `observation_timeout` - (float) additional time for
      detecting any unexpected messages when monitoring
      finishes
