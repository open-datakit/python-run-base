To run:

```
docker run -it -v ${DATAPACKAGE_PATH}:/usr/src/app/datapackage -e ALGORITHM=bindfit -e CONTAINER=ods/python-execution-base:v1 -e ARGUMENTS=bindfit.default ods/python-execution-base:v1
```
