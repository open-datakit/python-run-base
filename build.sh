#!/usr/bin/env bash

docker build -t opends/python-run-base:v0 -t opends/python-run-base:v0.1.2 -t opends/python-run-base:latest . $@
