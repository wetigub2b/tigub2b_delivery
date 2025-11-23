-- Migration: Create tigu_lookup table
-- Created: 2025-11-23
-- Description: Create lookup table for mapping numeric and string values to descriptions and table/column references

CREATE TABLE IF NOT EXISTS tigu_lookup (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Primary key, auto-generated',
    lookup_number INT COMMENT 'Numeric lookup value',
    lookup_string VARCHAR(100) COMMENT 'String lookup value',
    lookup_desc VARCHAR(100) COMMENT 'Description of the lookup value',
    map_table_name VARCHAR(100) COMMENT 'Referenced table name',
    map_column_name VARCHAR(100) COMMENT 'Referenced column name',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update timestamp'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Lookup table for mapping values to descriptions and table/column references';

-- Create indexes for better query performance
CREATE INDEX idx_lookup_number ON tigu_lookup(lookup_number);
CREATE INDEX idx_lookup_string ON tigu_lookup(lookup_string);
CREATE INDEX idx_map_table ON tigu_lookup(map_table_name, map_column_name);
