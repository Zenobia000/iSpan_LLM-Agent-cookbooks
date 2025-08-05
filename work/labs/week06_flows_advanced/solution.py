import sys
sys.path.append('/home/os-sunnie.gd.weng/python_workstation/side_project/crewai_system')

from src.core.flows import flow

@flow
def aqi_weather_alert(data: dict):
    """Analyzes air quality and weather data to issue a combined alert if necessary."""
    aqi = data.get("aqi")
    weather = data.get("weather")

    print(f"--- Analyzing Data: AQI is {aqi}, Weather is '{weather}' ---")

    if aqi is None or weather is None:
        print("  [INFO] Incomplete data. Skipping alert.")
        return

    # Advanced conditional logic
    if aqi > 150 and weather == "Rain":
        print("  [ALERT] High AQI and rain detected! It's recommended to stay indoors.")
    elif aqi > 150:
        print("  [WARNING] High AQI detected. Consider wearing a mask if you go outside.")
    elif weather == "Rain":
        print("  [INFO] It's raining. Don't forget your umbrella!")
    else:
        print("  [INFO] AQI and weather are normal. Enjoy your day!")

if __name__ == "__main__":
    # Scenario 1: High AQI, sunny weather
    scenario_1_data = {"aqi": 160, "weather": "Sunny"}
    aqi_weather_alert(scenario_1_data)

    # Scenario 2: Low AQI, rainy weather
    scenario_2_data = {"aqi": 50, "weather": "Rain"}
    aqi_weather_alert(scenario_2_data)

    # Scenario 3: High AQI, rainy weather (should trigger the main alert)
    scenario_3_data = {"aqi": 180, "weather": "Rain"}
    aqi_weather_alert(scenario_3_data)

    # Scenario 4: Normal conditions
    scenario_4_data = {"aqi": 80, "weather": "Cloudy"}
    aqi_weather_alert(scenario_4_data)
