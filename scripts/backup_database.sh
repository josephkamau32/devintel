#!/bin/bash

# Database Backup Script for DevIntel
# This script creates encrypted backups of the PostgreSQL database

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-devintel_db}"
DB_USER="${DB_USER:-devintel}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump not found. Please install PostgreSQL client tools."
        exit 1
    fi
    
    if ! command -v gpg &> /dev/null; then
        log_warn "gpg not found. Backups will not be encrypted."
        ENCRYPT=false
    else
        ENCRYPT=true
    fi
    
    if [ ! -d "$BACKUP_DIR" ]; then
        log_info "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi
}

# Create backup
create_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/devintel_backup_${timestamp}.sql"
    local compressed_file="${backup_file}.gz"
    local encrypted_file="${compressed_file}.gpg"
    
    log_info "Starting database backup..."
    
    # Dump database
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --format=custom \
        --file="$backup_file" \
        --verbose
    
    if [ $? -eq 0 ]; then
        log_info "Database dump completed: $backup_file"
    else
        log_error "Database dump failed"
        exit 1
    fi
    
    # Compress backup
    log_info "Compressing backup..."
    gzip "$backup_file"
    
    # Encrypt if gpg is available and key is provided
    if [ "$ENCRYPT" = true ] && [ -n "$ENCRYPTION_KEY" ]; then
        log_info "Encrypting backup..."
        echo "$ENCRYPTION_KEY" | gpg \
            --batch \
            --yes \
            --passphrase-fd 0 \
            --symmetric \
            --cipher-algo AES256 \
            --output "$encrypted_file" \
            "$compressed_file"
        
        # Remove unencrypted file
        rm "$compressed_file"
        log_info "Backup encrypted: $encrypted_file"
        FINAL_FILE="$encrypted_file"
    else
        log_warn "Backup not encrypted"
        FINAL_FILE="$compressed_file"
    fi
    
    # Get file size
    local file_size=$(du -h "$FINAL_FILE" | cut -f1)
    log_info "Backup completed: $FINAL_FILE ($file_size)"
    
    echo "$FINAL_FILE"
}

# Clean old backups
cleanup_old_backups() {
    log_info "Cleaning up backups older than $BACKUP_RETENTION_DAYS days..."
    
    find "$BACKUP_DIR" -name "devintel_backup_*.sql.gz*" -type f -mtime +$BACKUP_RETENTION_DAYS -delete
    
    local remaining=$(find "$BACKUP_DIR" -name "devintel_backup_*.sql.gz*" -type f | wc -l)
    log_info "Remaining backups: $remaining"
}

# Verify backup
verify_backup() {
    local backup_file=$1
    
    log_info "Verifying backup integrity..."
    
    if [[ "$backup_file" == *.gpg ]]; then
        # Verify encrypted file
        if [ -n "$ENCRYPTION_KEY" ]; then
            echo "$ENCRYPTION_KEY" | gpg --batch --passphrase-fd 0 --decrypt "$backup_file" > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                log_info "Backup verification successful"
                return 0
            else
                log_error "Backup verification failed"
                return 1
            fi
        fi
    else
        # Verify compressed file
        gzip -t "$backup_file" 2>&1
        if [ $? -eq 0 ]; then
            log_info "Backup verification successful"
            return 0
        else
            log_error "Backup verification failed"
            return 1
        fi
    fi
}

# Upload to cloud storage (optional)
upload_to_cloud() {
    local backup_file=$1
    
    if [ -n "$AWS_S3_BUCKET" ]; then
        log_info "Uploading to S3: $AWS_S3_BUCKET"
        aws s3 cp "$backup_file" "s3://$AWS_S3_BUCKET/backups/" --storage-class STANDARD_IA
        log_info "Upload completed"
    fi
}

# Main execution
main() {
    log_info "=== DevIntel Database Backup ===" 
    log_info "Started at: $(date)"
    
    check_prerequisites
    
    backup_file=$(create_backup)
    
    if verify_backup "$backup_file"; then
        cleanup_old_backups
        upload_to_cloud "$backup_file"
        
        log_info "=== Backup Completed Successfully ==="
        log_info "Finished at: $(date)"
        exit 0
    else
        log_error "Backup verification failed. Please check the backup file."
        exit 1
    fi
}

# Run main function
main
