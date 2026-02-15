#!/bin/bash

# Database Restore Script for DevIntel
# This script restores encrypted PostgreSQL backups

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-devintel_db}"
DB_USER="${DB_USER:-devintel}"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    if ! command -v pg_restore &> /dev/null; then
        log_error "pg_restore not found. Please install PostgreSQL client tools."
        exit 1
    fi
}

# List available backups
list_backups() {
    log_info "Available backups:"
    find "$BACKUP_DIR" -name "devintel_backup_*.sql.gz*" -type f -exec ls -lh {} \; | \
        awk '{print NR". "$9" ("$5")"}'
}

# Restore backup
restore_backup() {
    local backup_file=$1
    local temp_dir=$(mktemp -d)
    local sql_file="${temp_dir}/restore.sql"
    
    log_warn "This will OVERWRITE the current database: $DB_NAME"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "Restore cancelled"
        exit 0
    fi
    
    log_info "Starting restore from: $backup_file"
    
    # Decrypt if needed
    if [[ "$backup_file" == *.gpg ]]; then
        log_info "Decrypting backup..."
        echo "$ENCRYPTION_KEY" | gpg \
            --batch \
            --passphrase-fd 0 \
            --decrypt "$backup_file" | \
            gunzip > "$sql_file"
    else
        log_info "Decompressing backup..."
        gunzip -c "$backup_file" > "$sql_file"
    fi
    
    # Restore database
    log_info "Restoring database..."
    PGPASSWORD="$DB_PASSWORD" pg_restore \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --clean \
        --if-exists \
        --verbose \
        "$sql_file"
    
    # Cleanup
    rm -rf "$temp_dir"
    
    log_info "=== Restore Completed Successfully ==="
}

# Main
main() {
    log_info "=== DevIntel Database Restore ==="
    
    check_prerequisites
    
    if [ -z "$1" ]; then
        list_backups
        echo ""
        read -p "Enter backup filename or number: " selection
        
        # If number selected
        if [[ "$selection" =~ ^[0-9]+$ ]]; then
            backup_file=$(find "$BACKUP_DIR" -name "devintel_backup_*.sql.gz*" -type f | sed -n "${selection}p")
        else
            backup_file="$BACKUP_DIR/$selection"
        fi
    else
        backup_file=$1
    fi
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    restore_backup "$backup_file"
}

main "$@"
