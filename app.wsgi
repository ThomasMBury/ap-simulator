#! /usr/bin/python3.6

import logging
import sys
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/home/ubuntu/torord/myokit/dash_ap_explorer')
sys.path.insert(0,'/home/ubuntu/torord/myokit/dash_ap_explorer/venv/lib/python3.6/site-packages')
from app import server as application
application.secret_key = 'ap_explorer'
