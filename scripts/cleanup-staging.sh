#!/bin/bash

# Stop and remove all containers, volumes, and networks
echo "Stopping and removing Docker Compose services..."
docker-compose down -v

echo "Removing SSL certificates..."
rm -rf ssl/

echo "Staging environment cleaned up."
