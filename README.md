# Velarium

A centralized control panel for spinning up, monitoring and managing a minecraft network behind a Velocity proxy via a single web UI.

## 🎯 Features

- **Master API (FastAPI)**  
  • Spawn, list, start, stop, remove minecraft server containers  
  • Persistent metadata in PostgreSQL  
  • Admin-only access (HTTP Basic auth for now)  

- **Web UI (React + Tailwind)**  
  • File explorer / editor for each server’s config & plugins  
  • Dashboard showing container status & logs (via WebSockets)  
  • Create new server from template  

- **Dockerized**  
  • `docker-compose` brings up Postgres, backend, frontend  
  • Templates folder for default Velocity configs  
  • Dynamic container lifecycle, with world/plugin data persisted via volumes  

## 🚀 Quickstart
