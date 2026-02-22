"""Docker monitoring service."""
import docker
from datetime import datetime
from typing import List, Dict, Optional
import requests


class DockerMonitor:
    """Monitor Docker images, containers, and system info."""
    
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.available = True
        except Exception as e:
            print(f"Docker client not available: {e}")
            self.available = False
    
    def get_images(self) -> List[Dict]:
        """Get list of Docker images."""
        if not self.available:
            return []
        
        try:
            images = self.client.images.list()
            result = []
            
            for img in images:
                # Get the first tag or use <none>
                tags = img.tags if img.tags else ["<none>:<none>"]
                
                for tag in tags:
                    parts = tag.split(":")
                    repo = parts[0] if len(parts) > 0 else "<none>"
                    tag_name = parts[1] if len(parts) > 1 else "<none>"
                    
                    result.append({
                        "id": img.short_id.replace("sha256:", ""),
                        "repository": repo,
                        "tag": tag_name,
                        "size": round(img.attrs.get("Size", 0) / (1024 * 1024), 2),  # Size in MB
                        "created": img.attrs.get("Created", ""),
                    })
            
            # Sort by repository name
            result.sort(key=lambda x: x["repository"])
            return result
            
        except Exception as e:
            print(f"Error getting Docker images: {e}")
            return []
    
    def get_containers(self) -> List[Dict]:
        """Get list of Docker containers (running and stopped)."""
        if not self.available:
            return []
        
        try:
            containers = self.client.containers.list(all=True)
            result = []
            
            for container in containers:
                result.append({
                    "id": container.short_id,
                    "name": container.name,
                    "image": container.image.tags[0] if container.image.tags else container.image.short_id,
                    "status": container.status,
                    "state": container.attrs.get("State", {}).get("Status", "unknown"),
                    "created": container.attrs.get("Created", ""),
                    "ports": self._format_ports(container.attrs.get("NetworkSettings", {}).get("Ports", {}))
                })
            
            # Sort by name
            result.sort(key=lambda x: x["name"])
            return result
            
        except Exception as e:
            print(f"Error getting Docker containers: {e}")
            return []
    
    def _format_ports(self, ports_dict: Dict) -> str:
        """Format container ports for display."""
        if not ports_dict:
            return ""
        
        port_list = []
        for container_port, host_bindings in ports_dict.items():
            if host_bindings:
                for binding in host_bindings:
                    host_port = binding.get("HostPort", "")
                    if host_port:
                        port_list.append(f"{host_port}→{container_port}")
            else:
                port_list.append(container_port)
        
        return ", ".join(port_list) if port_list else ""
    
    def get_docker_info(self) -> Dict:
        """Get Docker system information."""
        if not self.available:
            return {
                "available": False,
                "error": "Docker is not available"
            }
        
        try:
            info = self.client.info()
            df = self.client.df()
            
            # Calculate disk usage - sum all sizes from df result
            images_size = 0
            containers_size = 0
            volumes_size = 0
            
            if df.get("Images"):
                images_size = sum(img.get("Size", 0) for img in df["Images"])
            
            if df.get("Containers"):
                containers_size = sum(c.get("SizeRw", 0) for c in df["Containers"])
            
            if df.get("Volumes"):
                volumes_size = sum(v.get("UsageData", {}).get("Size", 0) for v in df["Volumes"] if v.get("UsageData"))
            
            return {
                "available": True,
                "containers": {
                    "total": info.get("Containers", 0),
                    "running": info.get("ContainersRunning", 0),
                    "paused": info.get("ContainersPaused", 0),
                    "stopped": info.get("ContainersStopped", 0)
                },
                "images": {
                    "total": info.get("Images", 0)
                },
                "disk_usage": {
                    "images": round(images_size / (1024 * 1024 * 1024), 2),
                    "containers": round(containers_size / (1024 * 1024 * 1024), 2),
                    "volumes": round(volumes_size / (1024 * 1024 * 1024), 2)
                }
            }
        except Exception as e:
            print(f"Error getting Docker info: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    def get_jenkins_info(self, jenkins_url: str = "http://infrasentinel-jenkins:8080") -> Dict:
        """Get Jenkins build information."""
        try:
            # Try to get last build info from Jenkins API
            response = requests.get(
                f"{jenkins_url}/job/InfraSentinel/api/json",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                last_build = data.get("lastBuild", {})
                
                if last_build:
                    build_number = last_build.get("number", 0)
                    # Get detailed build info
                    build_response = requests.get(
                        f"{jenkins_url}/job/InfraSentinel/{build_number}/api/json",
                        timeout=5
                    )
                    
                    if build_response.status_code == 200:
                        build_data = build_response.json()
                        
                        return {
                            "available": True,
                            "job_name": data.get("name", "InfraSentinel"),
                            "last_build": {
                                "number": build_number,
                                "result": build_data.get("result", "IN_PROGRESS"),
                                "duration": round(build_data.get("duration", 0) / 1000, 2),  # Convert to seconds
                                "timestamp": build_data.get("timestamp", 0),
                                "url": build_data.get("url", "")
                            },
                            "health_score": data.get("healthReport", [{}])[0].get("score", 0) if data.get("healthReport") else 0
                        }
            
            return {
                "available": False,
                "error": "Jenkins not accessible or job not found"
            }
            
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }


# Global instance
docker_monitor = DockerMonitor()
