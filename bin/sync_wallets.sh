#!/bin/bash

docker-compose exec node1 cat wallet.dat > wallet1.dat
echo "Synced node1's wallet:"
./client.py balance --wallet wallet1.dat
echo

docker-compose exec node2 cat wallet.dat > wallet2.dat
echo "Synced node2's wallet:"
./client.py balance --wallet wallet2.dat