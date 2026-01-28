"""
Quick test script for smartwatch import functionality
"""
from ich_bp_agent.utils.smartwatch_import import import_smartwatch_file
from ich_bp_agent.analyzers.stability_analyzer import BPReading


def test_import():
    """Test importing sample smartwatch data"""
    print("Testing smartwatch import functionality...")
    print("=" * 60)

    # Read sample file
    try:
        with open('sample_smartwatch_data.json', 'r', encoding='utf-8') as f:
            file_content = f.read()
        print("✅ Sample file loaded successfully")
    except FileNotFoundError:
        print("❌ Sample file not found: sample_smartwatch_data.json")
        print("   Make sure you run this from the ich_bp_agent_github directory")
        return

    # Test import with empty existing readings
    try:
        existing_readings = []
        patient_id = "test_patient_001"

        merged_readings, stats = import_smartwatch_file(
            file_content,
            existing_readings,
            patient_id
        )

        print("\n📊 Import Statistics:")
        print("-" * 60)
        print(f"Total records in file:    {stats['total_records']}")
        print(f"Valid imports:            {stats['valid_imports']}")
        print(f"Invalid records:          {stats['invalid_records']}")
        print(f"Duplicates skipped:       {stats['duplicates_skipped']}")
        print(f"New records added:        {stats['new_records_added']}")
        print(f"Has heartrate data:       {stats['has_heartrate']} records")
        print(f"Has SpO2 data:            {stats['has_spo2']} records")

        print("\n📋 Sample Readings (first 5):")
        print("-" * 60)
        for i, reading in enumerate(merged_readings[:5]):
            print(f"{i+1}. {reading.timestamp.strftime('%Y-%m-%d %H:%M:%S')}: "
                  f"{reading.systolic}/{reading.diastolic} mmHg "
                  f"(source: {reading.source})")

        print("\n✅ Import test successful!")

        # Test duplicate detection
        print("\n🔄 Testing duplicate detection...")
        print("-" * 60)
        merged_readings2, stats2 = import_smartwatch_file(
            file_content,
            merged_readings,
            patient_id
        )

        print(f"New records added:        {stats2['new_records_added']}")
        print(f"Duplicates skipped:       {stats2['duplicates_skipped']}")

        if stats2['duplicates_skipped'] == stats['total_records']:
            print("✅ Duplicate detection working correctly!")
        else:
            print("⚠️ Unexpected duplicate detection result")

    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_import()
