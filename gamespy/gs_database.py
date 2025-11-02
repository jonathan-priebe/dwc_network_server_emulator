#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Improved script to add all ban checking methods to gs_database.py
This version ensures all four methods are present
"""

import re

# All four ban checking methods that need to be added
BAN_METHODS = '''    def is_ap_banned(self, postdata):
        if 'bssid' in postdata:
            with Transaction(self.conn) as tx:
                row = tx.queryone(
                    "SELECT COUNT(*) FROM banned WHERE banned_id = ? AND ubtime > ? AND type = 'ap'",
                    (postdata['bssid'], time.time())
                )
                return int(row[0]) > 0
        return False

    def is_ip_banned(self, postdata):
        with Transaction(self.conn) as tx:
            row_ = tx.queryone("SELECT setting_value from settings WHERE setting_name = 'ip_allowbanned'")
            result_ = int(row_[0])
            if result_ == 0:
                row = tx.queryone(
                    "SELECT COUNT(*) FROM banned WHERE banned_id = ? AND ubtime > ? AND type = 'ip'",
                    (postdata['ipaddr'], time.time())
                )
                return int(row[0]) > 0
            if result_ == 1:
                return False
        return False

    def is_console_macadr_banned(self, postdata):
        if 'macadr' in postdata:
            with Transaction(self.conn) as tx:
                row_ = tx.queryone("SELECT setting_value from settings WHERE setting_name = 'mac_allowbanned'")
                result_ = int(row_[0])
                if result_ == 0:
                    row = tx.queryone(
                        "SELECT COUNT(*) FROM banned WHERE banned_id = ? AND ubtime > ? and type = 'console'",
                        (postdata['macadr'], time.time())
                    )
                    return int(row[0]) > 0
                if result_ == 1:
                    return False
        return False

    def is_profile_banned(self, postdata):
        if 'gsbrcd' in postdata:
            with Transaction(self.conn) as tx:
                row_ = tx.queryone("SELECT setting_value from settings WHERE setting_name = 'profile_allowbanned'")
                result_ = int(row_[0])
                if result_ == 0:
                    row = tx.queryone(
                        "SELECT COUNT(*) FROM banned WHERE banned_id = ? AND ubtime > ? AND type = 'profile'",
                        (postdata['gsbrcd'], time.time())
                    )
                    return int(row[0]) > 0
                if result_ == 1:
                    return False
        return False

    def console_register(self, postdata):
        if 'csnum' in postdata:
            with Transaction(self.conn) as tx:
                row = tx.queryone("SELECT COUNT(*) FROM consoles WHERE macadr = ? and platform = 'wii'", (postdata['macadr'],))
                result = int(row[0])
                if result == 0:
                    row_ = tx.queryone("SELECT setting_value from settings WHERE setting_name = 'console_manualactivation'")
                    result_ = int(row_[0])
                    if result_ == 0:
                        tx.nonquery("INSERT INTO consoles (macadr, csnum, platform, enabled, abuse) VALUES (?,?,'wii','1','0')", (postdata['macadr'], postdata['csnum']))
                    if result_ == 1:
                        tx.nonquery("INSERT INTO consoles (macadr, csnum, platform, enabled, abuse) VALUES (?,?,'wii','0','0')", (postdata['macadr'], postdata['csnum']))
            return result > 0
        else:
            with Transaction(self.conn) as tx:
                row = tx.queryone("SELECT COUNT(*) FROM consoles WHERE macadr = ? and platform = 'other'", (postdata['macadr'],))
                result = int(row[0])
                if result == 0:
                    row_ = tx.queryone("SELECT setting_value from settings WHERE setting_name = 'console_manualactivation'")
                    result_ = int(row_[0])
                    if result_ == 0:
                        tx.nonquery("INSERT INTO consoles (macadr, platform, enabled, abuse) VALUES (?,'other','1','0')", (postdata['macadr'],))
                    if result_ == 1:
                        tx.nonquery("INSERT INTO consoles (macadr, platform, enabled, abuse) VALUES (?,'other','0','0')", (postdata['macadr'],))
            return result > 0

    def pending_console(self, postdata):
        with Transaction(self.conn) as tx:
            row = tx.queryone("SELECT COUNT(*) FROM consoles WHERE macadr = ? and enabled = 0", (postdata['macadr'],))
            return int(row[0]) > 0

    def allowed_games(self, postdata):
        with Transaction(self.conn) as tx:
            row = tx.queryone("SELECT COUNT(*) FROM allowed_games WHERE gamecd = ?", (postdata['gamecd'][:3],))
            return int(row[0]) > 0

    def console_abuse(self, postdata):
        # ONLY FOR WII CONSOLES
        if 'csnum' in postdata:
            with Transaction(self.conn) as tx:
                row = tx.queryone("SELECT COUNT(*) FROM consoles WHERE csnum = ?", (postdata['csnum'],))
                result = int(row[0])
                if result > 2:
                    tx.nonquery("UPDATE consoles SET abuse = 1 WHERE csnum = ?", (postdata['csnum'],))
                    return True
                else:
                    return False
        else:
            return False

    def valid_mac(self, postdata):
        return len(postdata["macadr"]) == 12'''

def fix_gs_database(filepath):
    """Fix the gs_database.py file by adding/replacing ban methods"""
    
    print(f"Reading file: {filepath}")
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Backup the original file
    backup_path = filepath + '.backup2'
    print(f"Creating backup at: {backup_path}")
    with open(backup_path, 'w') as f:
        f.write(content)
    
    # Remove any existing is_banned, is_*_banned, console_*, pending_console, allowed_games, valid_mac methods
    methods_to_remove = [
        'is_banned', 'is_ap_banned', 'is_ip_banned', 
        'is_console_macadr_banned', 'is_profile_banned',
        'console_register', 'pending_console', 'allowed_games',
        'console_abuse', 'valid_mac'
    ]
    
    for method in methods_to_remove:
        # Pattern to match entire method
        pattern = r'    def ' + method + r'\(self.*?\n(?=    def [a-z_]+\(self|\Z)'
        content = re.sub(pattern, '', content, flags=re.DOTALL)
        print(f"Removed old {method} method (if it existed)")
    
    # Find a good place to insert - after get_next_available_userid
    insert_pattern = r'(    def get_next_available_userid\(self\):.*?return userid\n)'
    
    match = re.search(insert_pattern, content, re.DOTALL)
    
    if match:
        print("Found insertion point after get_next_available_userid...")
        # Insert the new methods after get_next_available_userid
        insert_pos = match.end()
        new_content = content[:insert_pos] + '\n' + BAN_METHODS + '\n\n' + content[insert_pos:]
        
        # Write the fixed content
        print(f"Writing fixed content to: {filepath}")
        with open(filepath, 'w') as f:
            f.write(new_content)
        
        print("✅ Successfully added all ban checking methods to gs_database.py!")
        print("   Added methods:")
        print("   - is_ap_banned()")
        print("   - is_ip_banned()")
        print("   - is_console_macadr_banned()")
        print("   - is_profile_banned()")
        print("   - console_register()")
        print("   - pending_console()")
        print("   - allowed_games()")
        print("   - console_abuse()")
        print("   - valid_mac()")
        return True
    else:
        print("❌ Could not find insertion point in the file")
        return False

if __name__ == '__main__':
    import sys
    
    filepath = '/var/www/dwc_network_server_emulator/gamespy/gs_database.py'
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    
    success = fix_gs_database(filepath)
    sys.exit(0 if success else 1)