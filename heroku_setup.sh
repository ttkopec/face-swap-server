#!/usr/bin/env bash
# heroku login
# git add .
# git commit -m "Init"
# git push origin master
# heroku create face-swap-server
heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt
heroku buildpacks:add --index 2 heroku/python
# git push heroku master