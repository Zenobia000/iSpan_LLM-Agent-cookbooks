
# 修復 SQLite 版本兼容性 - 必須在導入 CrewAI 之前執行
import sys
try:
    import pysqlite3.dbapi2 as sqlite3
    sys.modules['sqlite3'] = sqlite3
    sys.modules['sqlite3.dbapi2'] = sqlite3
except ImportError:
    import sqlite3
    print(f"⚠️  使用系統 SQLite，版本: {sqlite3.sqlite_version}")

import os
import requests
from typing import Type
from pydantic import BaseModel, Field, validator
from crewai.tools import BaseTool

class CoordinateWeatherInput(BaseModel):
    """Input schema for coordinate-based weather lookup."""
    latitude: float = Field(
        ..., 
        description="Latitude coordinate (-90.0 to 90.0)",
        ge=-90.0,
        le=90.0,
        examples=[35.6762, 40.7128, 51.5074]
    )
    longitude: float = Field(
        ..., 
        description="Longitude coordinate (-180.0 to 180.0)",
        ge=-180.0,
        le=180.0,
        examples=[139.6503, -74.0060, -0.1278]
    )
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Latitude must be a number")
        if not -90.0 <= v <= 90.0:
            raise ValueError("Latitude must be between -90.0 and 90.0")
        return float(v)
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Longitude must be a number")
        if not -180.0 <= v <= 180.0:
            raise ValueError("Longitude must be between -180.0 and 180.0")
        return float(v)

class CoordinateWeatherTool(BaseTool):
    name: str = "CoordinateWeatherTool"
    description: str = """
    Fetches real-time weather data using precise latitude and longitude coordinates.
    
    Use this tool when you have exact coordinates for a location.
    
    Examples of correct usage:
    - latitude: 35.6762, longitude: 139.6503 (Tokyo)
    - latitude: 40.7128, longitude: -74.0060 (New York)
    - latitude: 51.5074, longitude: -0.1278 (London)
    
    ⚠️ Note: Coordinates must be decimal degrees (not degrees/minutes/seconds)
    """
    args_schema: Type[BaseModel] = CoordinateWeatherInput

    def _run(self, latitude: float, longitude: float) -> str:
        """
        Fetch weather data using coordinates.
        
        Args:
            latitude: Latitude coordinate (validated)
            longitude: Longitude coordinate (validated)
            
        Returns:
            Formatted weather information string
        """
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not api_key:
            return "❌ Error: OPENWEATHERMAP_API_KEY not found in environment variables."
        
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        
        # 使用坐標查詢
        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': api_key,
            'units': 'metric'
        }
            
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # 提取天氣資訊
            location_name = data.get('name', 'Unknown Location')
            country = data.get('sys', {}).get('country', 'Unknown')
            weather_description = data['weather'][0]['description'].title()
            temperature = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            pressure = data['main']['pressure']
            wind_speed = data.get('wind', {}).get('speed', 0) * 3.6  # 轉換為 km/h
            wind_deg = data.get('wind', {}).get('deg', 0)
            
            # 風向轉換
            wind_direction = self._get_wind_direction(wind_deg)
            
            # 格式化輸出
            result = f"""🌤️ Weather Report for Coordinates ({latitude}, {longitude})
📍 Location: {location_name}, {country}

Current Conditions: {weather_description}
🌡️ Temperature: {temperature}°C (feels like {feels_like}°C)
💧 Humidity: {humidity}%
🌪️ Pressure: {pressure} hPa
💨 Wind: {wind_speed:.1f} km/h {wind_direction}"""
            
            return result
            
        except requests.exceptions.Timeout:
            return "❌ Error: Request timeout. Please try again."
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 401:
                return "❌ Error: Invalid API key. Please check your OpenWeatherMap API key."
            elif response.status_code == 429:
                return "❌ Error: API rate limit exceeded. Please try again later."
            return f"❌ Error: HTTP error occurred: {http_err}"
        except requests.exceptions.RequestException as req_err:
            return f"❌ Error: Network error occurred: {req_err}"
        except KeyError as key_err:
            return f"❌ Error: Unexpected API response format: {key_err}"
        except Exception as e:
            return f"❌ Error: An unexpected error occurred: {e}"
    
    def _get_wind_direction(self, degrees: float) -> str:
        """Convert wind degrees to compass direction."""
        if degrees < 0 or degrees > 360:
            return "Unknown"
            
        directions = [
            "North", "North-Northeast", "Northeast", "East-Northeast",
            "East", "East-Southeast", "Southeast", "South-Southeast",
            "South", "South-Southwest", "Southwest", "West-Southwest",
            "West", "West-Northwest", "Northwest", "North-Northwest"
        ]
        
        index = round(degrees / 22.5) % 16
        return f"({directions[index]})"