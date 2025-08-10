#!/usr/bin/env python3
"""
Native .lnk file generator for Linux
Based on Microsoft Shell Link (.LNK) Binary File Format specification
https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-shllink/
"""

import struct
import uuid
import os
from datetime import datetime, timezone
from pathlib import Path
import time

class NativeLnkGenerator:
    """Native .lnk file generator without Windows dependencies"""
    
    # CLSID for Windows shortcuts
    SHELL_LINK_CLSID = uuid.UUID('00021401-0000-0000-C000-000000000046')
    
    # Flags for LinkFlags
    class LinkFlags:
        HasLinkTargetIDList = 0x00000001
        HasLinkInfo = 0x00000002
        HasName = 0x00000004
        HasRelativePath = 0x00000008
        HasWorkingDir = 0x00000010
        HasArguments = 0x00000020
        HasIconLocation = 0x00000040
        IsUnicode = 0x00000080
        ForceNoLinkInfo = 0x00000100
        HasExpString = 0x00000200
        RunInSeparateProcess = 0x00000400
        HasLogo3ID = 0x00000800
        HasDarwinID = 0x00001000
        RunAsUser = 0x00002000
        HasExpIcon = 0x00004000
        NoPidlAlias = 0x00008000
        ForceUncName = 0x00010000
        RunWithShimLayer = 0x00020000
        ForceNoLinkTrack = 0x00040000
        EnableTargetMetadata = 0x00080000
        DisableLinkPathTracking = 0x00100000
        DisableKnownFolderTracking = 0x00200000
        DisableKnownFolderAlias = 0x00400000
        AllowLinkToLink = 0x00800000
        UnaliasOnSave = 0x01000000
        PreferEnvironmentPath = 0x02000000
        KeepLocalIDListForUNCTarget = 0x04000000

    # ShowCommand values
    class ShowCommand:
        SW_HIDE = 0
        SW_NORMAL = 1
        SW_SHOWMINIMIZED = 2
        SW_SHOWMAXIMIZED = 3
        SW_SHOWNOACTIVATE = 4
        SW_SHOW = 5
        SW_MINIMIZE = 6
        SW_SHOWMINNOACTIVE = 7
        SW_SHOWNA = 8
        SW_RESTORE = 9
        SW_SHOWDEFAULT = 10

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset the generator to create a new shortcut"""
        self.target_path = ""
        self.arguments = ""
        self.working_directory = ""
        self.icon_location = ""
        self.icon_index = 0
        self.description = ""
        self.show_command = self.ShowCommand.SW_NORMAL
        self.hotkey = 0
        
    def set_target(self, path):
        """Set the target path of the shortcut"""
        self.target_path = str(path).replace('/', '\\')
        return self

    def set_arguments(self, args):
        """Set the command line arguments"""
        self.arguments = str(args) if args else ""
        return self

    def set_working_directory(self, workdir):
        """Set the working directory"""
        self.working_directory = str(workdir).replace('/', '\\') if workdir else ""
        return self

    def set_icon(self, icon_path, index=0):
        """Set the shortcut icon"""
        self.icon_location = str(icon_path).replace('/', '\\') if icon_path else ""
        self.icon_index = index
        return self

    def set_description(self, desc):
        """Set the shortcut description"""
        self.description = str(desc) if desc else ""
        return self

    def set_show_command(self, show_cmd):
        """Set the window display mode"""
        self.show_command = show_cmd
        return self

    def set_hotkey(self, key):
        """Set the keyboard shortcut key"""
        self.hotkey = key
        return self

    @staticmethod
    def _windows_filetime_now():
        """Convert current timestamp to Windows FILETIME format"""
        # FILETIME = number of 100-nanoseconds since 1601-01-01 00:00:00 UTC
        epoch_1601 = datetime(1601, 1, 1, tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - epoch_1601
        filetime = int(delta.total_seconds() * 10_000_000)
        return filetime

    def _encode_string_data(self, data):
        """Encode a string to UTF-16LE with length, compatible with old script"""
        if not data:
            return b'\x00\x00'
        
        # Encode like the old script: UTF-16 with BOM then remove BOM
        utf16_with_bom = data.encode('utf-16')
        utf16_data = utf16_with_bom.replace(b'\xff\xfe', b'')  # Remove BOM like old script
        
        length = len(data)  # Number of characters (not bytes)
        return struct.pack('<H', length) + utf16_data

    def _create_idlist_for_path(self, path):
        """Create a complete IDList compatible with Windows templates"""
        # Complete IDList structure like in Windows templates
        idlist_data = b''
        
        # Élément racine (My Computer) - GUID complet
        my_computer_guid = b'\xe0\x4f\xd0\x20\xea\x3a\x69\x10\xa2\xd8\x08\x00\x2b\x30\x30\x9d'
        root_item = b'\x1f\x50' + my_computer_guid
        idlist_data += struct.pack('<H', len(root_item) + 2) + root_item
        
        # Volume C:\ 
        volume_item = b'\x19\x00\x2f\x43\x3a\x5c' + b'\x00' * 13
        idlist_data += struct.pack('<H', len(volume_item) + 2) + volume_item
        
        # Windows folder
        windows_item = (b'\x52\x00\x31\x00\x00\x00\x00\x3c\x54\x2f\x7b\x10\x00'
                       b'Windows\x00\x3c\x00\x08\x00\x04\x00\xef\xbe\xee\x3a'
                       b'\xa3\x14\x3c\x54\x2f\x7b\x2a\x00\x00\x00\xf3\x01\x00'
                       b'\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00W\x00i\x00n\x00d\x00o\x00w\x00s\x00\x00\x00')
        idlist_data += struct.pack('<H', len(windows_item)) + windows_item
        
        # System32 folder  
        system32_item = (b'\x56\x00\x31\x00\x00\x00\x00\x72\x55\xfb\x2a\x10\x00'
                        b'System32\x00\x3e\x00\x08\x00\x04\x00\xef\xbe\xee\x3a'
                        b'\xa4\x14\x72\x55\xfb\x2a\x2a\x00\x00\x00\xf0\x06\x00'
                        b'\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                        b'\x00\x00\x00S\x00y\x00s\x00t\x00e\x00m\x00\x33\x00'
                        b'2\x00\x00\x00')
        idlist_data += struct.pack('<H', len(system32_item)) + system32_item
        
        # WindowsPowerShell folder
        powershell_folder_item = (b'\x68\x00\x31\x00\x00\x00\x00\xee\x3a\x90\x26\x10\x00'
                                 b'WINDOW~1\x00\x50\x00\x08\x00\x04\x00\xef\xbe\xee\x3a'
                                 b'\x90\x26\xee\x3a\x90\x26\x2a\x00\x00\x00\x10\x00\x00'
                                 b'\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                 b'\x00\x00\x00W\x00i\x00n\x00d\x00o\x00w\x00s\x00P\x00'
                                 b'o\x00w\x00e\x00r\x00S\x00h\x00e\x00l\x00l\x00\x00\x00')
        idlist_data += struct.pack('<H', len(powershell_folder_item)) + powershell_folder_item
        
        # v1.0 folder
        v10_folder_item = (b'\x4e\x00\x31\x00\x00\x00\x00\xee\x3a\x90\x26\x10\x00'
                          b'v1.0\x00\x3a\x00\x08\x00\x04\x00\xef\xbe\xee\x3a'
                          b'\x90\x26\xee\x3a\x90\x26\x2a\x00\x00\x00\x10\x00'
                          b'\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00'
                          b'\x00\x00\x00\x00\x00v\x001\x00.\x000\x00\x00\x00')
        idlist_data += struct.pack('<H', len(v10_folder_item)) + v10_folder_item
        
        # powershell.exe file
        powershell_exe_item = (b'\x5e\x00\x32\x00\x00\x08\x20\x20\xec\x21\xea\x3a\x69\x10'
                              b'\xa2\xdd\x08\x00\x2b\x30\x30\x9d\x19\x00\x2f\x43\x3a\x5c'
                              b'WINDOW~1\x5cv1.0\x5cpowershell.exe\x00\x48\x00\x08\x00\x04'
                              b'\x00\xef\xbe\xee\x3a\x90\x26\xee\x3a\x90\x26\x2a\x00\x00'
                              b'\x00\x20\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00'
                              b'\x00\x00\x00\x00\x00\x00p\x00o\x00w\x00e\x00r\x00s\x00'
                              b'h\x00e\x00l\x00l\x00.\x00e\x00x\x00e\x00\x00\x00')
        idlist_data += struct.pack('<H', len(powershell_exe_item)) + powershell_exe_item
        
        # Élément de fin
        idlist_data += b'\x00\x00'
        
        # Longueur totale de l'IDList
        total_length = len(idlist_data)
        return struct.pack('<H', total_length) + idlist_data

    def _create_link_info(self):
        """Crée la structure LinkInfo compatible avec les templates Windows"""
        # Structure LinkInfo complète comme dans le template original
        link_info = b''
        
        # LinkInfoSize (sera mis à jour à la fin)
        link_info_size_offset = len(link_info)
        link_info += b'\x00\x00\x00\x00'
        
        # LinkInfoHeaderSize
        link_info += struct.pack('<L', 0x1C)  # 28 bytes
        
        # LinkInfoFlags - VolumeIDAndLocalBasePath + CommonNetworkRelativeLink
        link_info_flags = 0x01  # VolumeIDAndLocalBasePath
        link_info += struct.pack('<L', link_info_flags)
        
        # VolumeIDOffset
        volume_id_offset = 0x1C
        link_info += struct.pack('<L', volume_id_offset)
        
        # LocalBasePathOffset  
        volume_id_size = 16  # Taille fixe du VolumeID
        local_base_path_offset = volume_id_offset + volume_id_size
        link_info += struct.pack('<L', local_base_path_offset)
        
        # CommonNetworkRelativeLinkOffset (0 = pas de réseau)
        link_info += struct.pack('<L', 0)
        
        # CommonPathSuffixOffset - utiliser le vrai target_path au lieu du hardcodé
        base_path = self.target_path  # Utiliser le vrai chemin cible
        common_path_suffix_offset = local_base_path_offset + len(base_path) + 1
        link_info += struct.pack('<L', common_path_suffix_offset)
        
        # VolumeID (structure simplifiée mais compatible)
        volume_id = struct.pack('<L', 16)  # VolumeIDSize
        volume_id += struct.pack('<L', 3)  # DriveType (DRIVE_FIXED)
        volume_id += struct.pack('<L', 0)  # DriveSerialNumber
        volume_id += struct.pack('<L', 16) # VolumeLabelOffset (pointe vers la fin)
        link_info += volume_id
        
        # LocalBasePath - utiliser le vrai chemin
        link_info += base_path.encode('ascii') + b'\x00'
        
        # CommonPathSuffix - extraire le nom du fichier du chemin cible
        import os
        suffix = os.path.basename(self.target_path)
        link_info += suffix.encode('ascii') + b'\x00'
        
        # Mettre à jour LinkInfoSize
        link_info_size = len(link_info)
        link_info = link_info[:link_info_size_offset] + struct.pack('<L', link_info_size) + link_info[link_info_size_offset + 4:]
        
        return link_info

    def generate(self, output_path):
        """Generate the .lnk file"""
        
        # Calculate flags based on present data
        flags = self.LinkFlags.HasLinkTargetIDList | self.LinkFlags.HasLinkInfo
        
        if self.arguments:
            flags |= self.LinkFlags.HasArguments
        if self.working_directory:
            flags |= self.LinkFlags.HasWorkingDir
        if self.icon_location:
            flags |= self.LinkFlags.HasIconLocation
        if self.description:
            flags |= self.LinkFlags.HasName
            
        # Always include HasRelativePath for compatibility with Windows templates
        flags |= self.LinkFlags.HasRelativePath
        flags |= self.LinkFlags.IsUnicode
        
        # Build the .lnk file
        lnk_data = b''
        
        # 1. Shell Link Header (76 bytes)
        header = b''
        
        # HeaderSize
        header += struct.pack('<L', 76)
        
        # LinkCLSID
        header += self.SHELL_LINK_CLSID.bytes_le
        
        # LinkFlags
        header += struct.pack('<L', flags)
        
        # FileAttributes
        header += struct.pack('<L', 0x00000020)  # FILE_ATTRIBUTE_ARCHIVE
        
        # CreationTime, AccessTime, WriteTime (FILETIME format)
        current_time = self._windows_filetime_now()
        for _ in range(3):
            header += struct.pack('<Q', current_time)
        
        # FileSize
        header += struct.pack('<L', 0)
        
        # IconIndex
        header += struct.pack('<L', self.icon_index)
        
        # ShowCommand
        header += struct.pack('<L', self.show_command)
        
        # Hotkey
        header += struct.pack('<H', self.hotkey)
        
        # Reserved (10 bytes)
        header += b'\x00' * 10
        
        lnk_data += header
        
        # 2. LinkTargetIDList
        if flags & self.LinkFlags.HasLinkTargetIDList:
            idlist = self._create_idlist_for_path(self.target_path)
            lnk_data += idlist
        
        # 3. LinkInfo
        if flags & self.LinkFlags.HasLinkInfo:
            link_info = self._create_link_info()
            lnk_data += link_info
        
        # 4. StringData
        
        # NAME_STRING (Description)
        if flags & self.LinkFlags.HasName:
            lnk_data += self._encode_string_data(self.description)
        
        # RELATIVE_PATH - toujours inclure pour compatibilité
        if flags & self.LinkFlags.HasRelativePath:
            lnk_data += self._encode_string_data(self.target_path)
        
        # WORKING_DIR
        if flags & self.LinkFlags.HasWorkingDir:
            lnk_data += self._encode_string_data(self.working_directory)
        
        # COMMAND_LINE_ARGUMENTS
        if flags & self.LinkFlags.HasArguments:
            lnk_data += self._encode_string_data(self.arguments)
        
        # ICON_LOCATION
        if flags & self.LinkFlags.HasIconLocation:
            lnk_data += self._encode_string_data(self.icon_location)
        
        # Écrire le fichier
        with open(output_path, 'wb') as f:
            f.write(lnk_data)
        
        return output_path

def create_powershell_lnk(target_command, output_path, icon_path=None, description=""):
    """
    Utility function to create a PowerShell shortcut
    Compatible with our existing interface
    """
    generator = NativeLnkGenerator()
    
    # PowerShell configuration
    powershell_path = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
    ps_args = f'-c "{target_command}"'
    
    # Generate the shortcut
    generator.set_target(powershell_path) \
            .set_arguments(ps_args) \
            .set_working_directory("%CD%") \
            .set_description(description or "PowerShell shortcut") \
            .set_show_command(NativeLnkGenerator.ShowCommand.SW_NORMAL)
    
    return generator.generate(output_path)

def create_powershell_lnk_simple(target_command, output_path, description=""):
    """
    Simplified version that uses the old script method
    Compatible with exact Windows template structure
    """
    # Use Windows template as base
    template_path = "template.lnk"  # Template in current directory
    if not os.path.exists(template_path):
        template_path = "lnk_generator/template.lnk"  # Fallback
        if not os.path.exists(template_path):
            # Fallback to complete method if no template
            return create_powershell_lnk(target_command, output_path, None, description)
    
    # Prepare command like old script
    command = f'"{target_command}"'
    
    # Calculate length for normal mode
    length_command = len(command) + 3  # for "-c "
    search_offset = 8
    
    # Read template (like old script)
    with open(template_path, 'rb') as f:
        s = f.read()
    
    # Search and replace command (exactly like old script)
    pattern = b'\x22\x00\x22\x00'  # "" in UTF-16
    loc_len_byte = s.find(pattern) - search_offset
    
    if loc_len_byte < 0:
        raise ValueError("Replacement pattern not found in template")
    
    # Patch correct length (like old script)
    s = s[:loc_len_byte] + length_command.to_bytes(2, byteorder='little') + s[loc_len_byte + 2:]
    
    # Replace with command (like old script)
    s = s.replace(pattern, bytes(command, 'utf-16'))
    
    # Remove encoding header (like old script)
    s = s.replace(b'\xff\xfe', b'')
    
    # Write file
    with open(output_path, 'wb') as f:
        f.write(s)
    
    return output_path

if __name__ == "__main__":
    # Quick test
    print("[*] Testing native .lnk generator...")
    
    # Create test shortcut
    test_output = "test_native.lnk"
    create_powershell_lnk("ping 8.8.8.8 -n 3", test_output)
    
    print(f"[+] Shortcut created: {test_output}")
    print(f"[+] Size: {os.path.getsize(test_output)} bytes")
    
    # Verify with file command
    import subprocess
    try:
        result = subprocess.run(['file', test_output], capture_output=True, text=True)
        if result.returncode == 0:
            file_type = result.stdout.split(':')[1].split(',')[0].strip()
            print(f"[+] Type: {file_type}")
    except:
        print("[-] 'file' command not available") 