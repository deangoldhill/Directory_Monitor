# Directory Monitor for Home Assistant

This custom integration monitors file and directory properties (file counts, size, creation/modification dates) from a remote Debian Linux server running the Directory Monitor API.

## Installation via HACS

1. Open HACS in your Home Assistant instance.
2. Click on the three dots in the top right corner and select **Custom repositories**.
3. Add the URL of this GitHub repository and select **Integration** as the category.
4. Click **Add** and then install the "Directory Monitor" integration.
5. Restart Home Assistant.

## Configuration

Add the following to your `configuration.yaml` file:

```yaml
sensor:
  - platform: dir_monitor
    update_interval: 60  # Optional: Polling interval in seconds (default: 300)
    servers:
      - host: "192.168.1.100"
        api_key: "YOUR_GENERATED_API_KEY_1"
      - host: "192.168.1.101"
        api_key: "YOUR_GENERATED_API_KEY_2"
