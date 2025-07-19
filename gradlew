#!/usr/bin/env sh

# Copyright 2011 the original author or authors.
# Licensed under the Apache License, Version 2.0

##############################################################################
#
#   Gradle start up script for UN*X
#
##############################################################################

DIR="$( cd "$( dirname "$0" )" && pwd )"
exec "$DIR/gradle/wrapper/gradle-wrapper.jar" "$@"
