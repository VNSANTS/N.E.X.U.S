# Android Termux deployment (Galaxy J6+)

This is an **experimental single-owner deployment** for a trusted personal device. It does not turn the current loopback-only WSGI app into a public service.

## Supported topology

- Galaxy J6+: Python application, SQLite database, and optional local worker.
- Moto G52: browser and SSH client.
- Both phones: Tailscale VPN for private device-to-device connectivity.
- N.E.X.U.S HTTP server: stays bound to `127.0.0.1:8765`; Do not port-forward it, bind it to `0.0.0.0`, or publish it through a public tunnel.
- Remote browser access: use an SSH local forward over the private VPN. The browser still talks to localhost, preserving the app's Host/origin protections.

The application currently requires Python 3.11+ and uses the Python standard library for its runtime. The Galaxy J6+ does not need to run a local LLM. Remote provider calls remain optional and must pass the existing provider allowlist and explicit budget controls.

## 1. Prepare the Galaxy J6+

1. Install Termux from one trusted distribution source (F-Droid or the official Termux GitHub releases). Install Termux:Boot from the same source if automatic startup is desired. Do not mix Termux add-ons from different signing sources.
2. Open Termux and run:

```sh
pkg update && pkg upgrade
pkg install git python openssh
python --version
```

Confirm Python is 3.11 or newer. If the package repository does not currently provide that version, stop here rather than weakening the project requirement.

3. Clone the repository and prepare a private working directory:

```sh
mkdir -p ~/apps
cd ~/apps
git clone https://github.com/VNSANTS/N.E.X.U.S.git
cd N.E.X.U.S
git switch nexus/remote-continuation
chmod 700 ~
```

4. Create the local environment file from the example. Keep API keys only on the Galaxy J6+:

```sh
cp .env.example .env
chmod 600 .env
nano .env
```

For the first local-only boot, keep these settings exactly disabled in `.env`:\n\n```dotenv\nNEXUS_ENABLE_REMOTE_PROVIDER=false\nNEXUS_REMOTE_PROVIDERS=\nNEXUS_MULTIAGENT_ENABLED=false\n```\n\nDo not enable remote providers until you have reviewed the provider's current free quota and configured an explicit budget in the N.E.X.U.S. UI. ChatGPT Go is not an API credit. Never commit `.env`, database files, backups, logs or tokens.

5. Initialize the database:

```sh
python -m nexus_learning --db "$HOME/nexus-data/nexus_learning.db" init
```

Create the data directory first with `mkdir -p "$HOME/nexus-data"` and `chmod 700 "$HOME/nexus-data"`.

## 2. Start the application

From the repository root:

```sh
sh scripts/termux-start.sh
```

The script starts the API in the foreground on loopback port 8765. Keep this Termux session alive. Open `http://127.0.0.1:8765/` on the Galaxy J6+ to create the first owner account. Use a unique password of at least 14 characters.

In a second Termux session, optionally start the worker:

```sh
sh scripts/termux-worker.sh
```

The worker and API must use the same database path. The worker is optional; do not enable autonomous research or recurring external calls just to keep it running.

## 3. Private access from the Moto G52

1. Install Tailscale on both phones and sign in to the same private tailnet. Do not enable Funnel or public sharing.
2. On the Galaxy J6+, configure OpenSSH for **public-key authentication only**. Generate a client key on the Moto G52 (Termux: `ssh-keygen -t ed25519`), add only its public key to the Galaxy J6+ `~/.ssh/authorized_keys`, and set permissions: `chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys`.
3. In the Galaxy J6+ Termux session, start SSH on port 8022:

```sh
sshd -p 8022
```

Disable password authentication in the Termux sshd configuration before relying on remote access. Do not expose port 8022 through router port forwarding. Keep the key private on the Moto G52.
4. Find the Galaxy J6+ Tailscale IPv4 address in the Tailscale app. On the Moto G52, use Termux to create a local forward (replace the address and Termux username):

```sh
ssh -N -L 8765:127.0.0.1:8765 -p 8022 USER@100.x.y.z
```

Keep that SSH session active. Open `http://127.0.0.1:8765/` in the Moto G52 browser. Traffic crosses the encrypted SSH tunnel; the N.E.X.U.S. app itself remains loopback-only.

If the Android Tailscale client does not route SSH to the device's Termux daemon on your device/OS build, stop and diagnose that separately. Do not solve it by exposing the N.E.X.U.S. HTTP port to the LAN or Internet.

## 4. Stability and recovery

- In Android settings, allow Termux to run in the background and exclude it from battery optimization where the OS permits.
- Run `termux-wake-lock` in the API session when supported. This reduces CPU sleep but does not guarantee uptime.
- Keep the phone powered, ventilated, and on a stable Wi-Fi connection. Android can still stop background processes after memory pressure, reboot, thermal events or OS updates.
- Termux:Boot can start a script after reboot, but it does not guarantee a production-grade always-on service. Test manual startup and recovery first.
- Stop the API and worker before restoring a database. Follow [DATABASE_BACKUP.md](DATABASE_BACKUP.md); keep backups private and off the Git repository.
- Do not run multiple API processes against this SQLite deployment.
- Check `GET /api/v1/health` locally and review the UI after restarting. Never claim the service is online unless you have checked it from the device.

## 5. Current limits

This setup is for personal testing, not production hosting. The app still has no TLS listener, production multi-user identity, public ingress, external secret manager, automatic process supervisor, or production retention controls. The SSH tunnel protects remote transport, but it does not add these missing application features.

The free-tier provider strategy remains fail-closed: no silent paid fallback, no automatic provider switch unless a provider is explicitly allowlisted and its budget permits the call. Model availability and free quotas can change; re-check each provider's current account limits before enabling it.
