"""
Smartwatch Data Import Utility
Handles import of blood pressure data from smartwatch JSON files
"""
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
from ich_bp_agent.models import BPReading


def parse_smartwatch_json(file_content: str) -> Dict[str, Any]:
    """
    Parse smartwatch JSON file

    Args:
        file_content: JSON file content as string

    Returns:
        Parsed JSON data as dictionary

    Raises:
        ValueError: If JSON is invalid or missing required fields
    """
    try:
        data = json.loads(file_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"無效的 JSON 格式: {e}")

    if not isinstance(data, dict):
        raise ValueError("JSON 資料應為物件格式")

    if 'bp' not in data:
        raise ValueError("找不到 'bp' 欄位（血壓資料）")

    if not isinstance(data['bp'], list):
        raise ValueError("'bp' 欄位應為陣列格式")

    return data


def convert_to_bp_readings(
    smartwatch_data: Dict[str, Any],
    patient_id: str = "imported"
) -> Tuple[List[BPReading], Dict[str, int]]:
    """
    Convert smartwatch BP data to BPReading objects

    Args:
        smartwatch_data: Parsed smartwatch JSON data
        patient_id: Patient ID to associate with readings

    Returns:
        Tuple of (list of BPReading objects, statistics dict)
    """
    bp_readings = []
    stats = {
        'total': len(smartwatch_data.get('bp', [])),
        'valid': 0,
        'invalid': 0,
        'has_heartrate': len(smartwatch_data.get('hb', [])),
        'has_spo2': len(smartwatch_data.get('spo2', [])),
    }

    for record in smartwatch_data.get('bp', []):
        try:
            # Validate required fields
            if not all(k in record for k in ['time', 'sys', 'dia']):
                stats['invalid'] += 1
                continue

            # Parse time - smartwatch format: "2024-10-16 10:15:00"
            time_str = record['time']
            # Convert to datetime
            if 'T' not in time_str:
                time_str = time_str.replace(' ', 'T')

            timestamp = datetime.fromisoformat(time_str.replace('Z', '+00:00'))

            # Create BPReading
            reading = BPReading(
                timestamp=timestamp,
                systolic=int(record['sys']),
                diastolic=int(record['dia']),
                patient_id=patient_id,
                source='smartwatch'  # Mark as imported from smartwatch
            )

            bp_readings.append(reading)
            stats['valid'] += 1

        except (ValueError, KeyError, TypeError) as e:
            stats['invalid'] += 1
            continue

    return bp_readings, stats


def merge_readings(
    existing_readings: List[BPReading],
    new_readings: List[BPReading]
) -> Tuple[List[BPReading], int]:
    """
    Merge new readings with existing ones, avoiding duplicates

    Args:
        existing_readings: Existing BP readings
        new_readings: New BP readings to add

    Returns:
        Tuple of (merged readings list, number of duplicates skipped)
    """
    # Create set of existing timestamps for quick lookup
    existing_timestamps = {r.timestamp for r in existing_readings}

    # Filter out duplicates
    unique_new_readings = [
        r for r in new_readings
        if r.timestamp not in existing_timestamps
    ]

    duplicates = len(new_readings) - len(unique_new_readings)

    # Merge and sort by timestamp (newest first)
    merged = existing_readings + unique_new_readings
    merged.sort(key=lambda x: x.timestamp, reverse=True)

    return merged, duplicates


def import_smartwatch_file(
    file_content: str,
    existing_readings: List[BPReading],
    patient_id: str = "imported"
) -> Tuple[List[BPReading], Dict[str, Any]]:
    """
    Complete workflow to import smartwatch data

    Args:
        file_content: JSON file content as string
        existing_readings: Existing BP readings
        patient_id: Patient ID to associate with readings

    Returns:
        Tuple of (merged readings list, import statistics)

    Raises:
        ValueError: If file format is invalid
    """
    # Parse JSON
    data = parse_smartwatch_json(file_content)

    # Convert to BPReading objects
    new_readings, conversion_stats = convert_to_bp_readings(data, patient_id)

    # Merge with existing readings
    merged_readings, duplicates = merge_readings(existing_readings, new_readings)

    # Compile statistics
    import_stats = {
        'total_records': conversion_stats['total'],
        'valid_imports': conversion_stats['valid'],
        'invalid_records': conversion_stats['invalid'],
        'duplicates_skipped': duplicates,
        'new_records_added': len(new_readings) - duplicates,
        'has_heartrate': conversion_stats['has_heartrate'],
        'has_spo2': conversion_stats['has_spo2'],
    }

    return merged_readings, import_stats
