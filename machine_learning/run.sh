#!/bin/bash
docker run --runtime=nvidia -u $(id -u):$(id -g) -it --rm -v $(realpath ~/git/ecen-715-project/machine_learning):/tf/notebooks -p 8888:8888 ecen715:latest
