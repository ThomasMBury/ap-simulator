#! /usr/bin/python3.8

import logging
import sys

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/home/ubuntu/ap-simulator")
sys.path.insert(0, "/home/ubuntu/ap-simulator/venv/lib/python3.8/site-packages")
from app_rate_dep import server as application

application.secret_key = "ap-simulator"