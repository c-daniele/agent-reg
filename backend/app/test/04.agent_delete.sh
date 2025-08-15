#!/bin/bash

# Assert 1 parameter is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <agent_id>"
    exit 1
fi

agent_id=$1

curl -X DELETE "http://localhost:8000/agents/$agent_id" -H "Content-Type: application/json"