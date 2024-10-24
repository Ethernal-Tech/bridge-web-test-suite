#!/bin/bash

sudo apt update
sudo wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -O /opt/google-chrome.deb
sudo apt install /opt/google-chrome.deb
sudo apt --fix-broken install
pip install -r requirements.txt
