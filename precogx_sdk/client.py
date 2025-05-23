import os
from typing import Dict, Any, Optional
import httpx
from dotenv import load_dotenv
from .models import TelemetryData
from .exceptions import PrecogXError, AuthenticationError, ValidationError

class PrecogXClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize the PrecogX client.
        
        Args:
            api_key: Your PrecogX API key. If not provided, will look for PRECOGX_API_KEY env var.
            api_url: The PrecogX API URL. If not provided, will look for PRECOGX_API_URL env var.
            timeout: Request timeout in seconds.
        """
        load_dotenv()
        
        self.api_key = api_key or os.getenv("PRECOGX_API_KEY")
        if not self.api_key:
            raise AuthenticationError("API key not provided and PRECOGX_API_KEY not found in environment")
            
        self.api_url = api_url or os.getenv("PRECOGX_API_URL", "https://api.precogx.ai")
        self.timeout = timeout
        self.client = httpx.Client(
            base_url=self.api_url,
            timeout=timeout,
            headers={"x-api-key": self.api_key}
        )
    
    def send_telemetry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send telemetry data to the PrecogX API.
        
        Args:
            data: Telemetry data dictionary matching the TelemetryData model.
            
        Returns:
            Dict containing the API response.
            
        Raises:
            PrecogXError: If the API request fails.
            ValidationError: If the data doesn't match the expected schema.
        """
        try:
            # Validate the data using our Pydantic model
            telemetry_data = TelemetryData(**data)
            
            # Send the request
            response = self.client.post(
                "/api/v1/telemetry",
                json=telemetry_data.model_dump()
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif e.response.status_code == 422:
                raise ValidationError(f"Invalid data format: {e.response.text}")
            else:
                raise PrecogXError(f"API request failed: {str(e)}")
        except httpx.RequestError as e:
            raise PrecogXError(f"Request failed: {str(e)}")
        except Exception as e:
            raise PrecogXError(f"Unexpected error: {str(e)}")
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 