#!/bin/bash
# Quick run script for Docker

docker-compose -f docker/docker-compose.yml run --rm gdrive-sync "$@"
