#!/bin/bash
docker compose up -d
trap "docker compose down" SIGINT
docker logs api_arq_flask -f -t
