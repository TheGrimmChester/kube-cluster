# Build and tag image
sudo docker build -t registry.${REGISTRY}/bw-cli:latest .
sudo docker push thegrimmchester/bw-cli
