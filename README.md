# Network Toolkit

A desktop network diagnostics and monitoring application built with Python and CustomTkinter. Combines speed testing, network troubleshooting tools, local device scanning, and network info lookup into a single dark-themed GUI app.

## Overview

Network Toolkit is an all-in-one utility for checking and diagnosing network performance and connectivity. It measures download/upload speed and ping against multiple global servers, provides standard network diagnostic tools (ping, traceroute, DNS lookup, port checking), scans the local network for connected devices, and displays detailed public/local network information — all without leaving one application.

## Tech Stack

- **Python**
- **CustomTkinter** — modern dark-themed GUI
- **Matplotlib** — live speed history graphing
- **Requests** — HTTP-based speed testing and API calls
- **Socket / Subprocess** — DNS lookups, port checks, ping, and traceroute

## Key Features

### ⚡ Speed Test
- Download, upload, and ping measurement
- Selectable test servers (Fast.com/Netflix CDN, UK, USA, Germany, Singapore, South Africa)
- Live speed history graph
- Configurable low-speed alert threshold
- Copy results to clipboard
- Export test history to CSV

### 🔧 Network Tools
- Custom ping with min/avg/max response times
- Traceroute to any host or IP
- DNS lookup (domain → IP resolution)
- Port checker (open/closed status on a given host and port)

### 🖥️ Device Scanner
- Scans the local subnet (1–254) for active devices
- Displays IP address, hostname, and online status for each device found

### 🌍 My Info
- Local IP address and hostname
- Public IP, ISP, city, region, country, and timezone (via ipinfo.io)
- One-click refresh

## Requirements

- Python 3.x
- `customtkinter`
- `requests`
- `matplotlib`

Install dependencies:
