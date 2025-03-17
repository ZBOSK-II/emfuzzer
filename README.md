How to run:
`python -m coapper --config experiment_config.json data/*.bin`

Get help:
`python -m coapper --help`

Using Docker:

Call `./build.sh`, then:

`./coapper.sh --config config.json /data/*.bin`.

Docker container mounts:
 - current (working) directory
 - `/data`
