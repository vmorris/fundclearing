## Prerequisites

- python3
- python-virtualenv

## Getting Started

- Clone the repo, ensure that the submodules are included.

```bash
mkdir ~/git; cd ~/git
git clone --recurse-submodules https://github.com/vmorris/fundclearing.git
cd fundclearing
```

- Setup python virtualenv and install sdk

```bash
virtualenv env -p python3
source env/bin/activate
pip install ./fund_clearing_python_sdk
```

## Deploy local Fabric network, Fund Clearing Business Network and REST Servers

- Setup local composer development environment.
Follow the instructions at https://hyperledger.github.io/composer/latest/installing/development-tools.html
Once you have the local environment running (including the Fabric network), continue.

- Clone the Composer sample networks repo.

```bash
cd ~/git
git clone https://github.com/hyperledger/composer-sample-networks.git
```

- Run the script to reset the Fabric network, deploy the business network, and start the REST servers.

```bash
cd ~/git/fundclearing/dev
./reset.sh
```

## Start the Fund Clearing Application

- Ensure your virtual environment is activated.

```bash
cd ~/git/fundclearing
source env/bin/activate
```

- Start the application.

```bash
python app.py
```

## Extra

- You can start composer playground if you have it installed and interact with the network through it as well.
- The `reset.sh` script will completely reset the local development environmet. Use with care!