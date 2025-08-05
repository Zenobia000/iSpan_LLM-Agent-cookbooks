import sys
sys.path.append('/home/os-sunnie.gd.weng/python_workstation/side_project/crewai_system')

from src.core.flows import flow

@flow
def check_weather_conditions(city: str, temperature_threshold: float):
    """Checks the weather conditions for a given city and triggers an alert if the temperature exceeds a threshold."""
    # In a real-world scenario, this would involve an API call to a weather service.
    # For this example, we'll use a mock temperature.
    mock_temperature = 28.0

    print(f"Checking weather for {city}. Current temperature is {mock_temperature}°C.")

    if mock_temperature > temperature_threshold:
        print(f"ALERT: Temperature in {city} has exceeded the threshold of {temperature_threshold}°C!")

if __name__ == "__main__":
    check_weather_conditions("Taipei", 25.0)
