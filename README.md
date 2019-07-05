# HowToApp: An app to support learning for people with intellectual disability

This app is a video search engine and social media site to support learning for
persons with intellectual disabilities. It allows searching for videos using
textual and speech input. The search engine is limited to "how-to" videos.
Found videos can be shared to friends with basic social media features such as
commenting.  The user interface contains accessibility features such as
familiar iconography, simple and lean pages, prompts, accessible speech
input...

## Technical description

The search engine uses the Youtube data API to retrive videos limited to the "how-to" category. Search can be restricted to a target channel for directing users to specific content.

The server is written in python 3.7 using aiohttp for asynchroneous queries, and mongodb for data storage. 

# Requirements

- To build js scripts: node, npm
- To run the server in a virtualenv: python3.7, virtualenv, all the above
- To build the docker image: docker, all the above

# Running

HowToApp can be run as a docker container, or directly from a python virtual environment.

## Configuration file

A configuration file named src/secrets.py needs to be filled with parameters and secret API tokens. The template `src/secrets.template.py` can be used as model.

First, generate a secure token for signing session data in cookies.
~~~~
# install the cryptography python module if you don't already have it
pip3 install --user cryptography
# generate a secure token for authenticating cookies in the app
python3 src/secrets.template.py | tee src/secrets.py
~~~~

Then, fill the rest of the config file with corresponding values.

## Building the docker container

Use `make build` to create the container image from scratch.

## Creating a SSL certifacte for localhost (optional)

You can run the app on https://localhost:8787, but for that you need to
generate and trust a certificate for localhost. This step requires openssl to
be installed.
~~~~
cd ssl
./generate.sh
~~~~
Close all browser windows to force it to reload certificates.

## Running the docker container

The container needs to be bound to four volumes:
* `/app/src/secrets.py`: your dutifully filled configuration file
* `/app/ssl/localhost.key`: the ssl key for your host
* `/app/ssl/localhost.crt`: the ssl certificate for your host
* `/app/data`: the data directory which will contain the mongdb database, users information and random data for populating the app

Then use the makefile to run the app.
~~~~
make run
~~~~

To run it on port 443, use `-p 443:8787` in the `docker run` command line.

To stop the container, use `docker stop`, otherwise the mongodb database will be corrupted.

## Running using a virtualenv

Install python3.7, mongodb, gcc, libffi, libuv, (with development files) then
create the environment:
~~~~
virtualenv -p python3.7 env
. env/bin/activate
pip install -r requirements.txt
~~~~

You can run the app with:
~~~~
. env/bin/activate
./run.sh
~~~~

