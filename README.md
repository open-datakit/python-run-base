# opendata.studio python-run-base

The base execution container for opendata.studio datakits.

All custom datakit containers must inherit from _python-run-base_.

## Development

### Building

```bash
./build.sh [--no-cache]
```

### Running

To run a datakit in _python-run-base_ manually:

```bash
docker run -it -v ${DATAKIT_PATH}:/usr/src/app/datakit -e RUN=bindfit.run opends/python-run-base:latest
```

### Pushing to DockerHub

Ensure all version numbers are updated in `build.sh` and the correct tags are applied by `docker image ls`. Remove any old tags.

```bash
docker image push --all-tags opends/python-run-base
```
