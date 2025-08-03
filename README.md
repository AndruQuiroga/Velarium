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
_Work-in-progress — full instructions coming as the stack solidifies._

## 🛠️ Roadmap / TODO

### Core functionality

- [ ] **Authentication & authorization**
  - Single-admin login using session or token-based auth
  - Optional expansion to multi-user accounts with roles/permissions
- [ ] **Docker image builder for server templates**
  - Build Paper, Forge, or Fabric images on demand with specified versions
  - Support optional CurseForge/Modrinth project identifiers for modpacks
  - Cache and reuse previously built images to reduce build time
- [ ] **Server lifecycle management**
  - Create, start, stop, restart, and delete individual server containers
  - Persist world and plugin data on dedicated Docker volumes
  - Track server status, ports, and data paths in PostgreSQL
- [ ] **Velocity proxy integration**
  - Dynamically generate `velocity.toml` based on active servers
  - Manual restart endpoint with optional auto-restart toggle
  - Hot-reload proxy config when servers are added/removed
- [ ] **Web UI dashboard**
  - Display all registered servers with current state indicators
  - Provide buttons for start/stop/restart and live status polling
  - Stream server logs via WebSockets with auto-scroll
- [ ] **File explorer**
  - Browse server directories with path sandboxing for security
  - Upload, download, and delete files
  - Edit text files in-browser with syntax highlighting and save support
  - Show file metadata such as size, type, and last modified time
- [ ] **Plugin & mod management**
  - List installed plugins/mods with version metadata
  - Check for updates via Spiget, Modrinth, or CurseForge APIs
  - Download and replace plugin jars with one click, with rollback on failure
- [ ] **Persistent configuration and data**
  - Record all server details and user preferences in PostgreSQL
  - Ensure each container uses dedicated volumes for world and config data
  - Document backup and restore procedures for volumes

### Optional enhancements

- [ ] **Multi-user role system** with admin, operator, and viewer permissions
- [ ] **Scheduled tasks & backups** including automatic world saves and plugin update checks
- [ ] **Resource monitoring** graphs for CPU, RAM, and disk usage per server
- [ ] **One-click modpack deployment** from ZIP files or curated lists
- [ ] **Web-based console** to send commands directly to running servers
- [ ] **Metrics & analytics** such as player counts over time and audit logs
- [ ] **Discord/Slack notifications** for server events and alerts
- [ ] **Themeable UI** with light/dark modes and custom color schemes
- [ ] **Plugin marketplace** browser and search within the panel
- [ ] **OAuth or external identity provider integration**
- [ ] **REST & GraphQL APIs** for external automation and integrations
- [ ] **Mobile-friendly layout** optimized for phones and tablets

### Future ideas

- [ ] Auto-scaling or cluster support across multiple Docker hosts
- [ ] Kubernetes deployment option
- [ ] Snapshot-based backups and restore points
- [ ] Integration with metrics stacks (Prometheus/Grafana)
- [ ] Localization and internationalization support

