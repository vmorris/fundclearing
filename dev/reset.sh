#!/usr/bin/env bash

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
