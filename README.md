How to run:
`python -m emfuzzer --config experiment_config.json data/*.bin`

Get help:
`python -m emfuzzer --help`

Using Docker:

Call `./build.sh`, then:

`./emfuzzer.sh --config config.json /data/*.bin`.

Docker container mounts:
 - current (working) directory
 - `/data`
