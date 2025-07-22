# Database Configuration Guide

Trigger Deploy mendukung dua mode database:

1. **Local PostgreSQL** (default) - Database berjalan di Docker container
2. **External PostgreSQL** - Database server eksternal

## 🔧 Quick Switch Database

### Menggunakan Script Helper

```bash
# Lihat konfigurasi saat ini
./scripts/switch-database.sh config

# Test koneksi database saat ini
./scripts/switch-database.sh test

# Switch ke database lokal (Docker)
./scripts/switch-database.sh local

# Switch ke database eksternal
./scripts/switch-database.sh external 30.30.30.11 5456 mydb myuser mypass
```

### Manual Configuration

#### Untuk Database Eksternal (30.30.30.11:5456):

1. **Edit `.env` file:**
```bash
POSTGRES_DB=mydb
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypass
POSTGRES_HOST=30.30.30.11
POSTGRES_PORT=5456
DATABASE_URL=postgresql://myuser:mypass@30.30.30.11:5456/mydb
```

2. **Edit `docker-compose.yml` untuk external access:**
```yaml
# Uncomment untuk external database
network_mode: host

# Comment out untuk external database  
# networks:
#   - dev-trigger-network
# depends_on:
#   postgres:
#     condition: service_healthy
```

3. **Test konektivitas:**
```bash
python3 scripts/test-db-connectivity.py
```

4. **Restart aplikasi:**
```bash
docker-compose down
docker-compose up -d
```

#### Untuk Database Lokal (Docker):

1. **Edit `.env` file:**
```bash
POSTGRES_DB=trigger_deploy
POSTGRES_USER=trigger_deploy_user
POSTGRES_PASSWORD=secure_password_123
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql://trigger_deploy_user:secure_password_123@postgres:5432/trigger_deploy
```

2. **Edit `docker-compose.yml` untuk local docker:**
```yaml
# Comment out untuk local database
# network_mode: host

# Uncomment untuk local database
networks:
  - dev-trigger-network
depends_on:
  postgres:
    condition: service_healthy
```

3. **Restart aplikasi:**
```bash
docker-compose down
docker-compose up -d
```

## 🔒 SSL Configuration

Untuk koneksi database yang aman, atur SSL di `.env`:

```bash
POSTGRES_SSL_MODE=require          # disable, allow, prefer, require, verify-ca, verify-full
POSTGRES_SSL_CERT_PATH=/path/to/client.crt
POSTGRES_SSL_KEY_PATH=/path/to/client.key  
POSTGRES_SSL_CA_PATH=/path/to/ca.crt
```

## 🧪 Testing Tools

### Test Konektivitas Database
```bash
# Test dengan environment saat ini
python3 scripts/test-db-connectivity.py

# Atau menggunakan helper script
./scripts/switch-database.sh test
```

### Test Manual dengan psql
```bash
# Test koneksi eksternal
psql postgresql://myuser:mypass@30.30.30.11:5456/mydb

# Test koneksi lokal
psql postgresql://trigger_deploy_user:secure_password_123@localhost:5432/trigger_deploy
```

### Test Network Connectivity
```bash
# Test ping
ping 30.30.30.11

# Test port accessibility
telnet 30.30.30.11 5456
# atau
nc -zv 30.30.30.11 5456
```

## 🚀 Production Deployment

### Untuk Production dengan Database Eksternal:

1. **Konfigurasi environment:**
```bash
./scripts/switch-database.sh external 30.30.30.11 5456 mydb myuser mypass
```

2. **Verify koneksi:**
```bash
./scripts/switch-database.sh test
```

3. **Deploy:**
```bash
docker-compose down
docker-compose up -d
```

### Untuk Development dengan Database Lokal:

1. **Konfigurasi environment:**
```bash
./scripts/switch-database.sh local
```

2. **Deploy dengan PostgreSQL lokal:**
```bash
docker-compose down
docker-compose up -d
```

## 🔍 Troubleshooting

### Masalah Koneksi ke Database Eksternal

1. **Check network connectivity:**
```bash
ping 30.30.30.11
telnet 30.30.30.11 5456
```

2. **Check firewall settings:**
   - Pastikan port 5456 terbuka di server database
   - Pastikan IP aplikasi diizinkan mengakses database

3. **Check credentials:**
   - Verify username/password benar
   - Pastikan user memiliki akses ke database

4. **Check SSL requirements:**
   - Beberapa PostgreSQL server memerlukan SSL
   - Set `POSTGRES_SSL_MODE=require` jika diperlukan

### Masalah Docker Network

1. **Jika menggunakan external database, gunakan host network:**
```yaml
network_mode: host
```

2. **Jika error "postgres not found", pastikan:**
   - Menggunakan `localhost` untuk akses dari host
   - Menggunakan `postgres` untuk akses dari dalam container

### Log dan Debugging

1. **Check application logs:**
```bash
docker-compose logs dev-trigger-deploy
```

2. **Check database logs:**
```bash
docker-compose logs postgres
```

3. **Check database manager logs dalam aplikasi:**
   - Look for PostgreSQL connection messages
   - Check initialization status

## 📋 Configuration Summary

| Setting | Local Database | External Database |
|---------|---------------|------------------|
| POSTGRES_HOST | `postgres` | `30.30.30.11` |
| POSTGRES_PORT | `5432` | `5456` |
| POSTGRES_DB | `trigger_deploy` | `mydb` |
| POSTGRES_USER | `trigger_deploy_user` | `myuser` |
| POSTGRES_PASSWORD | `secure_password_123` | `mypass` |
| Docker Network | `dev-trigger-network` | `host` |
| Depends On | postgres service | none |
