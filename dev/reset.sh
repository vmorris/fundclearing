#!/usr/bin/env bash

# Copyright 2018 International Business Machines
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

CLEARING_VERSION=0.2.6

TMP_DIR=$(mktemp -d)
echo "Temp directory: ${TMP_DIR}"

# stop rest servers
for i in $(ps x| grep composer-rest-server | awk '{print $1}'); do 
	kill $i
done

# tear down previous fabric network
${HOME}/fabric-dev-servers/teardownFabric.sh
for i in $(composer card list -q); do composer card delete -c $i; done

# start new fabric network
${HOME}/fabric-dev-servers/startFabric.sh
${HOME}/fabric-dev-servers/createPeerAdminCard.sh

# setup clean
composer archive create \
    -t dir \
    -n ${HOME}/git/composer-sample-networks/packages/fund-clearing-network \
    -a ${TMP_DIR}/fund-clearing-network.bna

composer network install \
    -a ${TMP_DIR}/fund-clearing-network.bna \
    -c PeerAdmin@hlfv1

composer network start \
    -n fund-clearing-network \
    -V ${CLEARING_VERSION} \
    -A admin \
    -S adminpw \
    -c PeerAdmin@hlfv1 \
    -f ${TMP_DIR}/networkadmin.card

composer card import \
    -f ${TMP_DIR}/networkadmin.card

composer participant add -d \
'{
  "$class": "org.clearing.BankingParticipant",
  "bankingId": "bank1",
  "bankingName": "US Bank 1",
  "workingCurrency": "USD",
  "fundBalance": 1000000
}' \
    -c admin@fund-clearing-network

composer participant add -d \
'{
  "$class": "org.clearing.BankingParticipant",
  "bankingId": "bank2",
  "bankingName": "Euro Bank 2",
  "workingCurrency": "EURO",
  "fundBalance": 1000000
}' \
    -c admin@fund-clearing-network

composer identity issue \
    -u bank1 \
    -a org.clearing.BankingParticipant#bank1 \
    -c admin@fund-clearing-network \
    -f ${TMP_DIR}/bank1@fund-clearing-network.card

composer card import \
    -f ${TMP_DIR}/bank1@fund-clearing-network.card

composer identity issue \
    -u bank2 \
    -a org.clearing.BankingParticipant#bank2 \
    -c admin@fund-clearing-network \
    -f ${TMP_DIR}/bank2@fund-clearing-network.card

composer card import \
    -f ${TMP_DIR}/bank2@fund-clearing-network.card

composer-rest-server -c bank1@fund-clearing-network -n never -w true -p 3001 &
composer-rest-server -c bank2@fund-clearing-network -n never -w true -p 3002 &
