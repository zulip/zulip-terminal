# Docker

Docker is an operating system level virtualization solution for delivering software in packages called containers.

We assume users have Docker correctly installed on their computer if they wish to use this feature. Docker is available for Linux as well as MacOS and Windows. For more details visit: https://www.docker.com/

# Running Zulip Terminal with Docker

## Quick Start

To run `zulip-terminal` with docker, take the following steps:

```sh
# Clone the repository and change to where the docker files reside
git clone --depth=1 git@github.com:zulip/zulip-terminal.git
cd zulip-terminal/docker

# Build the docker image with your preferred Dockerfile, here based on Alpine

# To build the image with the latest release from PyPI.
docker build -t zulip-terminal:latest -f Dockerfile.alpine .

# Run zulip-terminal image and setup your zulip for the first time
# (next time the $HOME/.zulip/zuliprc file will be used)
mkdir $HOME/.zulip
docker run -it -v $HOME/.zulip:/.zulip zulip-terminal:latest
```

## Advanced Setup

Images built using the `docker build` command above, implicitly use `SOURCE=pypi` to run the [latest pypi release of Zulip-Terminal](https://pypi.org/project/zulip-term/). If you wish to use the latest code available in development (main) branch of the zulip-terminal repository then `SOURCE=git` can be passed as a build argument.

```sh
# To build docker image with the latest code in the main branch
docker build -t zulip-terminal:latest -f Dockerfile.alpine . --build-arg SOURCE=git

# In case you want to build the image with code from another branch, use GIT_URL to pass the appropriate remote and branch names
docker build -t zulip-terminal:latest -f Dockerfile.alpine . --build-arg SOURCE=git --build-arg GIT_URL=https://github.com/zulip/zulip-terminal.git@main
```

You can swap `Dockerfile.alpine` for `Dockerfile.buster` if you prefer running inside image based on Debian instead of Alpine. The main advantage of Alpine is a better use of resources. The final Alpine docker image has a size of 150MB while the Debian image takes 221MB of disk space.

