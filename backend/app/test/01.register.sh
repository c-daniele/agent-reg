#!/bin/bash

# Assert 1 parameter is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <file>"
    exit 1
fi

file=$1

curl -X POST "http://localhost:8000/agents/register" -H "Content-Type: application/json" -d @$file