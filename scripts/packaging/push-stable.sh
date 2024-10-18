#!/usr/bin/env bash -xe
#
# For the developer to run when a new release is made.
#
# The "stable" branch contains the latest release version of the project.
#
git checkout master
git push origin master

git checkout stable
git rebase master
git push origin stable

git checkout master
