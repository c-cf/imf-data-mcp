def process_imf_data(json_data: dict) -> str:
    """
    Process IMF data and return a string with the information.
    :param:
        json_data(dict): JSON data from the IMF API
    :return:
        (str) A string with the information from the JSON data
    """
    try:
       
        json_data = json_data["CompactData"]
        dataset = json_data["DataSet"]

        series_list = dataset["Series"]
        if isinstance(series_list, dict):
            series_list = [series_list]
        elif not isinstance(series_list, list):
            return f"Error: Expected series_list to be a list but got {type(series_list)}"

        output_texts = []
        
        for series in series_list:
            if series is None:
                output_texts.append("Warning: No indicator value.")
                continue
            country = series.get("@REF_AREA", None)
            obs = series.get("Obs", {})
            if isinstance(obs, dict):
                obs = [obs]
            elif not isinstance(obs, list):
                return f"Error: Expected obs to be a list but got {type(obs)}"
            for _obs in obs:
                if _obs is None:
                    output_texts.append(
                        f"Warning: No indicator value for {country} in that Year, You should not try to access the data of this country."
                    )
                    continue
                time_period = _obs.get("@TIME_PERIOD", "that Year")
                obs_value = _obs.get("@OBS_VALUE")
                
                if obs_value is not None:
                    text = f"In {time_period}, {country} had an indicator value of {float(obs_value):.2f}."
                    output_texts.append(text)
                else:
                    output_texts.append(f"Warning: No indicator value for {country} in {time_period}.")
        
        return "\n".join(output_texts)
    except KeyError as e:
        return f"Error processing IMF data: Missing key {str(e)}"
    except Exception as e:
        return f"Error processing IMF data: {str(e)}"
