#!/bin/bash

cd ~/Data_Science/
source env/bin/activate
export ELASTIC_PASSWORD="elastic"
py crawl.py &> crawl.log
