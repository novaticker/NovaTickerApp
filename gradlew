#!/usr/bin/env sh

##############################################################################
##
##  Gradle start up script for UN*X
##
##############################################################################

# Add default JVM options here. You can also use JAVA_OPTS and GRADLE_OPTS to pass JVM options to this script.
DEFAULT_JVM_OPTS=""

APP_NAME="Gradle"
APP_BASE_NAME=$(basename "$0")

# Resolve the location of the Gradle distribution.
if [ -n "$GRADLE_HOME" ] ; then
  GRADLE_USER_HOME="$GRADLE_HOME"
else
  GRADLE_USER_HOME="$HOME/.gradle"
fi

CLASSPATH=$GRADLE_USER_HOME/wrapper/dists

# Determine if we're in a Git repo
if [ -d ".git" ] || git rev-parse --git-dir > /dev/null 2>&1; then
  GIT_REPO=true
else
  GIT_REPO=false
fi

# Setup JAVA_HOME
if [ -z "$JAVA_HOME" ] ; then
  echo "ERROR: JAVA_HOME is not set and no 'java' command could be found in your PATH."
  echo "Please set the JAVA_HOME variable in your environment to match the location of your Java installation."
  exit 1
fi

JAVA_CMD="$JAVA_HOME/bin/java"
if [ ! -x "$JAVA_CMD" ] ; then
  echo "ERROR: JAVA_HOME is set to an invalid directory: $JAVA_HOME"
  echo "Please set the JAVA_HOME variable in your environment to match the location of your Java installation."
  exit 1
fi

# Execute Gradle
exec "$JAVA_CMD" $DEFAULT_JVM_OPTS -cp "$CLASSPATH" org.gradle.wrapper.GradleWrapperMain "$@"
