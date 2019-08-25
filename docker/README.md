# Docker

Docker is an operating system level virtualization solution for delivering software in packages called containers.

We asume use to have Docker installed on his computer. Docker is available for Linux as well as MacOS or even Windows. For more details visit: https://www.docker.com/

# Run Zulip Terminal with Docker

To run `zulip-terminal` with docker you have to do following steps:

```sh
# Clone repository and change current directory to it
git clone --depth=1 git@github.com:zulip/zulip-terminal.git
cd zulip-terminal/docker

# Now we have access to docker directory

# To build docker image with prefered Dockerfile, here based on Alpine
docker build -t zulip-terminal:latest -f docker/Dockerfile.alpine .

# Run zulip-terminal image and setup your zulip for the first time
# next time $HOME/.zulip/zuliprc file will be used
mkdir $HOME/.zulip
docker run -it -v $HOME/.zulip:/.zulip zulip-terminal:latest
```

You can swap `docker/Dockerfile.alpine` for `docker/Dockerfile.buster` if you prefer running inside image based on Debian over Alpine. The main advantage of Alpine is a better use of resources. Final Alpine docker image has a size of 150MB while Debian image takes 221MB of disk space. 

Currently dockerfiles contain instructions to use `zulip-terminal` version
published to PyPI and source code in the repository is not used.
