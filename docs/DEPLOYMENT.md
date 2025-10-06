# Production Deployment Guide

This guide explains how to run the OpenReview MCP Server in production.

## Option 1: systemd (Recommended for Linux)

systemd is the best option for production Linux servers. It provides automatic restart on failure, logging, and system integration.

### Setup

1. **Edit the service file** (`openreview-mcp.service`):
   ```bash
   # Update these paths:
   # - User=your-username
   # - WorkingDirectory=/path/to/openreview-mcp
   # - Environment="PATH=/path/to/openreview-mcp/.venv/bin:..."
   # - ExecStart=/path/to/openreview-mcp/.venv/bin/python -m src.server
   ```

2. **Create log directory**:
   ```bash
   sudo mkdir -p /var/log/openreview-mcp
   sudo chown your-username:your-username /var/log/openreview-mcp
   ```

3. **Install the service**:
   ```bash
   sudo cp openreview-mcp.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable openreview-mcp
   ```

### Usage

```bash
# Start the server
sudo systemctl start openreview-mcp

# Stop the server
sudo systemctl stop openreview-mcp

# Restart the server
sudo systemctl restart openreview-mcp

# Check status
sudo systemctl status openreview-mcp

# View logs
sudo journalctl -u openreview-mcp -f

# View recent errors
sudo journalctl -u openreview-mcp -n 100 --no-pager
```
---

## Option 2: Docker (Future Enhancement)

Docker deployment is planned but not yet implemented. This would provide:
- Isolated environment
- Easy deployment across platforms
- Container orchestration support (Kubernetes, etc.)

---

## Monitoring and Troubleshooting

### Check if server is running

```bash
# Check process
ps aux | grep openreview-mcp

# Check port is listening
netstat -tulpn | grep 3000
# or
ss -tulpn | grep 3000

# Test server response
curl http://localhost:3000/health
```

### View logs

```bash
# systemd
sudo journalctl -u openreview-mcp -f
```

### Common issues

1. **Port already in use**
   ```bash
   # Find what's using the port
   lsof -i :3000

   # Kill the process or change MCP_PORT
   ```

2. **Permission denied**
   ```bash
   # Make sure user has permissions
   sudo chown -R your-username:your-username /path/to/openreview-mcp
   ```

3. **Server crashes on startup**
   ```bash
   # Check logs for errors
   tail -100 logs/server.log

   # Test manually first
   uv run openreview-mcp
   ```

---

## Security Considerations

### Firewall

If accessing from external networks:

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 3000/tcp
```

---

## Backup and Maintenance

### Logs rotation

Logs are already configured with rotation in the application (10MB max, 5 backups).

For system logs:
```bash
# systemd handles this automatically
```

### Updates

```bash
# Stop server
sudo systemctl stop openreview-mcp

# Update code
git pull

# Update dependencies
uv sync

# Start server
sudo systemctl start openreview-mcp
```
