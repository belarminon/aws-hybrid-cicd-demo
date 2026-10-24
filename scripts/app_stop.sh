#!/bin/bash
cd /var/www/aws-hybrid-cicd-demo
docker-compose -p aws-pet-owner-app down --remove-orphans || true