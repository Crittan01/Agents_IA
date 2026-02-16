# awx_integration/awx_client.py
"""
Cliente para interactuar con AWX API
"""

import requests
import time
import json
from typing import Dict, Optional
from requests.auth import HTTPBasicAuth
from .config import AWX_CONFIG

class AWXClient:
    """Cliente para AWX API"""
    
    def __init__(self):
        self.base_url = AWX_CONFIG["base_url"]
        self.auth = HTTPBasicAuth(
            AWX_CONFIG["username"],
            AWX_CONFIG["password"]
        )
        self.verify_ssl = AWX_CONFIG["verify_ssl"]
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def get_job_template_id(self, template_name: str) -> Optional[int]:
        """Obtiene el ID de un job template por nombre"""
        url = f"{self.base_url}/api/v2/job_templates/"
        
        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            
            templates = response.json()["results"]
            for template in templates:
                if template["name"] == template_name:
                    return template["id"]
            
            return None
        
        except Exception as e:
            print(f"Error obteniendo template: {str(e)}")
            return None
    
    def launch_job(
        self, 
        template_id: int, 
        extra_vars: Dict
    ) -> Optional[int]:
        """Lanza un job y retorna el job_id"""
        url = f"{self.base_url}/api/v2/job_templates/{template_id}/launch/"
        
        payload = {
            "extra_vars": json.dumps(extra_vars)
        }
        
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=payload,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            
            job_id = response.json()["id"]
            return job_id
        
        except Exception as e:
            print(f"Error lanzando job: {str(e)}")
            return None
    
    def get_job_status(self, job_id: int) -> Dict:
        """Obtiene el status de un job"""
        url = f"{self.base_url}/api/v2/jobs/{job_id}/"
        
        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            
            job_data = response.json()
            return {
                "status": job_data["status"],
                "finished": job_data.get("finished", None),
                "failed": job_data.get("failed", False),
                "elapsed": job_data.get("elapsed", 0)
            }
        
        except Exception as e:
            print(f"Error obteniendo status: {str(e)}")
            return {"status": "error", "failed": True}
    
    def wait_for_job(self, job_id: int, timeout: int = 300) -> Dict:
        """Espera a que un job termine y retorna el resultado"""
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                return {
                    "status": "timeout",
                    "failed": True,
                    "message": "Job excedió el tiempo máximo de espera"
                }
            
            status = self.get_job_status(job_id)
            
            if status["status"] in ["successful", "failed", "error", "canceled"]:
                return status
            
            time.sleep(5)  # Esperar 5 segundos antes de verificar de nuevo
    
    def get_job_output(self, job_id: int) -> str:
        """Obtiene el output/log de un job"""
        url = f"{self.base_url}/api/v2/jobs/{job_id}/stdout/"
        
        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers,
                params={"format": "txt"},
                verify=self.verify_ssl
            )
            response.raise_for_status()
            return response.text
        
        except Exception as e:
            return f"Error obteniendo output: {str(e)}"