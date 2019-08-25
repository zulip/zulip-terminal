# Docker

Docker is an operating system level virtualization solution for delivering software in packages called containers.

We assume users have Docker correctly installed on their computer if they wish to use this feature. Docker is available for Linux as well as MacOS and Windows. For more details visit: https://www.docker.com/

# Running Zulip Terminal with Docker

To run `zulip-terminal` with docker, take the following steps:

```sh
# Clone the repository and change to where the docker files reside
git clone --depth=1 git@github.com:zulip/zulip-terminal.git
cd zulip-terminal/docker

# Build the docker image with your preferred Dockerfile, here based on Alpine
docker build -t zulip-terminal:latest -f Dockerfile.alpine .

# Run zulip-terminal image and setup your zulip for the first time
# (next time the $HOME/.zulip/zuliprc file will be used)
mkdir $HOME/.zulip
docker run -it -v $HOME/.zulip:/.zulip zulip-terminal:latest
```

You can swap `Dockerfile.alpine` for `Dockerfile.buster` if you prefer running inside image based on Debian instead of Alpine. The main advantage of Alpine is a better use of resources. The final Alpine docker image has a size of 150MB while the Debian image takes 221MB of disk space.

**NOTE**: The current Dockerfiles contain instructions to use the `zulip-terminal` version published to PyPI and source code in the repository is not used.
