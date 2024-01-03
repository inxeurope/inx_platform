#!/bin/bash

source /root/inx_platform/inx_platform/venv/bin/activate
cd /root/inx_platform/inx_platform/
exec gunicorn inx_platform.wsgi:application -w 2 -b 0.0.0.0:8000
