def process_imf_data(json_data: dict) -> str:
    """
    Parse an IMF CompactData API response into human-readable text.

    Args:
        json_data: Parsed JSON response from the IMF CompactData endpoint.

    Returns:
        str: One line per observation, or warning/error messages.
    """
    try:
        dataset = json_data["CompactData"]["DataSet"]
        series_list = dataset["Series"]

        if series_list is None:
            return "Warning: No data returned (empty series)."
        elif isinstance(series_list, dict):
            series_list = [series_list]
        elif not isinstance(series_list, list):
            return f"Error: Expected a list of series, got {type(series_list).__name__}."

        output: list[str] = []

        for series in series_list:
            if series is None:
                output.append("Warning: No indicator value.")
                continue

            country = series.get("@REF_AREA", "unknown")
            obs = series.get("Obs")

            if obs is None:
                output.append(
                    f"Warning: No data for {country}. "
                    "This country/indicator combination may not be available."
                )
                continue

            if isinstance(obs, dict):
                obs = [obs]
            elif not isinstance(obs, list):
                output.append(f"Error: Unexpected observation format for {country}.")
                continue

            for entry in obs:
                if entry is None:
                    output.append(f"Warning: Missing observation entry for {country}.")
                    continue

                time_period = entry.get("@TIME_PERIOD", "unknown period")
                obs_value = entry.get("@OBS_VALUE")

                if obs_value is not None:
                    output.append(
                        f"In {time_period}, {country} had an indicator value of {float(obs_value):.2f}."
                    )
                else:
                    output.append(
                        f"Warning: No indicator value for {country} in {time_period}."
                    )

        return "\n".join(output) if output else "No data returned."

    except KeyError as e:
        return f"Error processing IMF data: missing key {e}."
    except Exception as e:
        return f"Error processing IMF data: {e}"
