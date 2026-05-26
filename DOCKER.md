# Build & run

## 1. Install docker & docker-compose

```bash
# Debian / Ubuntu
sudo apt update
sudo apt install docker docker-compose

# Arch
sudo pacman -Sy
sudo pacman -S docker docker-compose
```

## 2. Run

```bash
docker-compose up --build
```

To stop use `docker-compose down`