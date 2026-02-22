"""Docker and Jenkins monitoring routes."""
from fastapi import APIRouter, Depends
from typing import Dict, List
from ..auth import get_current_user
from ..services.docker_monitor import docker_monitor


router = APIRouter(prefix="/api/docker", tags=["docker"])


@router.get("/images")
async def get_docker_images(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Get list of Docker images.
    
    Returns:
        List of Docker images with repository, tag, size, and created date
    """
    images = docker_monitor.get_images()
    return {
        "images": images,
        "count": len(images)
    }


@router.get("/containers")
async def get_docker_containers(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Get list of Docker containers.
    
    Returns:
        List of Docker containers with status and details
    """
    containers = docker_monitor.get_containers()
    return {
        "containers": containers,
        "count": len(containers)
    }


@router.get("/info")
async def get_docker_info(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Get Docker system information.
    
    Returns:
        Docker system info including container counts and disk usage
    """
    return docker_monitor.get_docker_info()


@router.get("/jenkins")
async def get_jenkins_info(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Get Jenkins build information.
    
    Returns:
        Jenkins job and build information
    """
    return docker_monitor.get_jenkins_info()
