"""
utils.py was removed in v0.2.0.

The old process_imf_data() helper parsed the now-defunct CompactData JSON
format from dataservices.imf.org. The new implementation delegates all
parsing to the imfp library, which handles the current data.imf.org API.
"""
