#!/usr/bin/env python3
"""
Convert RIPE NCC delegated statistics to CIDR notation.
Usage: python3 ripe-to-cidr.py <delegated-file> <country-code> <ipv4|ipv6>
"""

import sys
import math


def count_to_cidr_prefix(count):
    """Convert a host count to a CIDR prefix length."""
    return 32 - int(math.log2(count))


def split_to_cidrs_v4(start_ip, count):
    """Split a range into valid CIDR blocks."""
    cidrs = []
    parts = list(map(int, start_ip.split('.')))
    ip_num = (parts[0] << 24) + (parts[1] << 16) + (parts[2] << 8) + parts[3]
    
    remaining = count
    current = ip_num
    
    while remaining > 0:
        # Find the largest power of 2 that:
        # 1. Is <= remaining
        # 2. The current IP is aligned to
        max_size = remaining
        # Find alignment
        if current != 0:
            trailing_zeros = 0
            temp = current
            while temp & 1 == 0 and trailing_zeros < 32:
                trailing_zeros += 1
                temp >>= 1
            max_alignment = 1 << trailing_zeros
            max_size = min(max_size, max_alignment)
        
        # Find largest power of 2 <= max_size
        size = 1
        while size * 2 <= max_size:
            size *= 2
        
        prefix = 32 - int(math.log2(size))
        
        # Convert back to dotted notation
        a = (current >> 24) & 0xFF
        b = (current >> 16) & 0xFF
        c = (current >> 8) & 0xFF
        d = current & 0xFF
        
        cidrs.append(f"{a}.{b}.{c}.{d}/{prefix}")
        
        current += size
        remaining -= size
    
    return cidrs


def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <delegated-file> <country-code> <ipv4|ipv6>", file=sys.stderr)
        sys.exit(1)
    
    delegated_file = sys.argv[1]
    country_code = sys.argv[2].upper()
    ip_version = sys.argv[3].lower()
    
    with open(delegated_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split('|')
            if len(parts) < 7:
                continue
            
            registry, cc, record_type, start, value, date, status = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6] if len(parts) > 6 else ''
            
            if cc != country_code:
                continue
            
            if ip_version == 'ipv4' and record_type == 'ipv4':
                count = int(value)
                cidrs = split_to_cidrs_v4(start, count)
                for cidr in cidrs:
                    print(cidr)
            
            elif ip_version == 'ipv6' and record_type == 'ipv6':
                prefix_len = value
                print(f"{start}/{prefix_len}")


if __name__ == '__main__':
    main()
