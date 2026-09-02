# swarm-oom-exporter
```
services:
  stealth_rdap_exporter:
    build: ./docker/Dockerfile
    ports:
      - "9223:9223"
    restart: unless-stopped
```
