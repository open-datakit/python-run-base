To run:

```
docker run -it -v ${DATAPACKAGE_PATH}:/usr/src/app/datapackage -e ALGORITHM=bindfit -e CONTAINER=opendatafit/python-execution-base:v1 -e ARGUMENTS=bindfit.default opendatafit/python-execution-base:v1
```
