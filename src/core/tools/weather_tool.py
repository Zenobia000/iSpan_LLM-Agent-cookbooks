
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
from typing import Type, Optional
from pydantic import BaseModel, Field, validator
from crewai.tools import BaseTool

class CityWeatherInput(BaseModel):
    """Input schema for city-based weather lookup."""
    city_name: str = Field(
        ..., 
        description="City name (e.g., 'Tokyo', 'New York', 'London'). Use simple city names without country codes.",
        examples=["Tokyo", "New York", "London", "Paris", "Sydney"]
    )
    
    @validator('city_name')
    def validate_city_name(cls, v):
        if not v or not v.strip():
            raise ValueError("City name cannot be empty")
        
        # 清理輸入
        cleaned = v.strip()
        
        # 檢查是否包含經緯度格式 (lat,lon)
        if ',' in cleaned and cleaned.replace(',', '').replace('.', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError("This tool accepts city names only. For coordinates, use a different tool.")
        
        # 移除常見的後綴以標準化輸入
        common_suffixes = [', Japan', ', USA', ', UK', ', China', ', France']
        for suffix in common_suffixes:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
                break
                
        return cleaned


# 已經實作單點當下天氣 沒有實作過去一段時間天氣

class OpenWeatherMapTool(BaseTool):
    name: str = "OpenWeatherMapTool"
    description: str = """
    Fetches real-time weather data for cities worldwide.
    
    ⚠️ IMPORTANT: This tool ONLY accepts city names (e.g., 'Tokyo', 'London', 'New York').
    DO NOT use coordinates, country codes, or complex location strings.
    
    Examples of correct usage:
    - city_name: "Tokyo"
    - city_name: "London" 
    - city_name: "New York"
    
    Examples of INCORRECT usage:
    - "Tokyo, Japan" (remove country)
    - "35.6762,139.6503" (coordinates not supported)
    - "NYC" (use full name)
    """
    args_schema: Type[BaseModel] = CityWeatherInput

    def _run(self, city_name: str) -> str:
        """
        Fetch weather data for a specific city.
        
        Args:
            city_name: Clean city name (already validated by input schema)
            
        Returns:
            Formatted weather information string
        """
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not api_key:
            return "❌ Error: OPENWEATHERMAP_API_KEY not found in environment variables."
        
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        
        # 使用城市名查詢
        params = {
            'q': city_name,
            'appid': api_key,
            'units': 'metric'
        }
            
        try:
            response = requests.get(base_url, params=params, timeout=10)
            
            if response.status_code == 404:
                return f"❌ Error: City '{city_name}' not found. Please check the spelling or try a different city name."
            
            response.raise_for_status()
            data = response.json()
            
            # 提取天氣資訊
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
            result = f"""🌤️ Weather Report for {data['name']}, {data['sys']['country']}

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
