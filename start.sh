#!/usr/bin/env bash
sudo pserve production.ini --reload

python do_turns.py
