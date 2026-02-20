"""Nmap wrapper for structured service discovery."""
import subprocess
import shutil
import re
import xml.etree.ElementTree as ET
from jupiter.safety.broker import ToolResult

def get_local_cidr() -> str:
    """Detect local network CIDR."""
    try:
        # Get default route interface
        r = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True)
        # e.g. "default via 10.0.2.2 dev eth0 proto dhcp src 10.0.2.15 metric 100"
        m = re.search(r"dev\s+(\S+)", r.stdout)
        if not m: return "127.0.0.1"
        iface = m.group(1)
        
        # Get IP/CIDR for interface
        r = subprocess.run(["ip", "-o", "-f", "inet", "addr", "show", iface], capture_output=True, text=True)
        # e.g. "2: eth0    inet 10.0.2.15/24 brd 10.0.2.255 scope global dynamic eth0"
        m = re.search(r"inet\s+([0-9\./]+)", r.stdout)
        return m.group(1) if m else "127.0.0.1"
    except Exception:
        return "127.0.0.1"


def scan_network(target: str, ports: str = "top-100", speed: int = 4) -> ToolResult:
    """Run Nmap scan and return structured service info."""
    if target == "auto":
        target = get_local_cidr()
        
    if not shutil.which("nmap"):
        return ToolResult(success=False, output="", error="Nmap not found. Install: sudo apt install nmap")

    # Construct command
    # -sV: Service version detection
    # -oX -: Output XML to stdout
    # -T4: Speed
    # --open: Only show open ports
    cmd = ["nmap", "-sV", "-T" + str(speed), "--open", "-oX", "-"]
    
    if ports == "all":
        cmd.append("-p-")
    elif ports == "top-100":
        cmd.extend(["--top-ports", "100"])
    else:
        cmd.extend(["-p", ports])
        
    cmd.append(target)
    
    try:
        # Run scan
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return ToolResult(success=False, output=res.stdout, error=res.stderr, audit_action="nmap_fail")
            
        # Parse XML
        try:
            root = ET.fromstring(res.stdout)
        except ET.ParseError:
            return ToolResult(success=False, output=res.stdout, error="Failed to parse Nmap XML output", audit_action="nmap_parse_error")
            
        services = []
        output_lines = [f"Nmap Scan Results for {target}:"]
        
        for host in root.findall("host"):
            address = host.find("address").get("addr")
            ports_elem = host.find("ports")
            if ports_elem:
                for port in ports_elem.findall("port"):
                    port_id = port.get("portid")
                    protocol = port.get("protocol")
                    service = port.find("service")
                    
                    if service is not None:
                        name = service.get("name", "unknown")
                        product = service.get("product", "")
                        version = service.get("version", "")
                        full_version = f"{product} {version}".strip()
                        
                        services.append({
                            "port": port_id,
                            "protocol": protocol,
                            "name": name,
                            "version": full_version
                        })
                        output_lines.append(f"  - Port {port_id}/{protocol}: {name} ({full_version})")
                    else:
                        output_lines.append(f"  - Port {port_id}/{protocol}: unknown")
                        
        if not services:
            return ToolResult(success=True, output=f"No open ports found on {target} (scanned {ports}).", audit_action="nmap_empty")
            
        # Suggest next steps
        output_lines.append("\n[SUGGESTION] Found versions. You should run exploit_search() for specific versions.")
        
        return ToolResult(
            success=True, 
            output="\n".join(output_lines), 
            audit_action="nmap_scan_success"
        )

    except Exception as e:
        return ToolResult(success=False, output="", error=f"Nmap execution failed: {str(e)}", audit_action="nmap_exception")
