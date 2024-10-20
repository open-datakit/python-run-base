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
docker run -it -v ${DATAKIT_PATH}:/usr/src/app/datakit -e RUN=bindfit.run opends/python-run-base:v1
```

### Pushing to DockerHub

```bash
docker push opends/python-run-base:v1
```
