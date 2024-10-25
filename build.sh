#!/usr/bin/env bash

docker build -t datakits/python-run-base:v0 -t datakits/python-run-base:v0.2 -t datakits/python-run-base:latest . $@
