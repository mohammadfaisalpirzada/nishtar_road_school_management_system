#!/usr/bin/env python3
"""
Background sync worker for School Management System
Runs periodic sync of data between Google Sheets
"""

import os
import time
from dotenv import load_dotenv
from web_app import data_entry, data_cache

def run_sync():
    """Run continuous background sync"""
    print("Starting background sync worker...")
    
    while True:
        try:
            print("🔄 Background sync started...")
            # Sync all data
            if data_entry:
                all_students = data_entry.get_all_students()
                data_cache.set_all_data(all_students)
                print("✅ All students synced")
                
                # Get class-wise data
                class_data = data_entry.get_class_wise_data()
                data_cache.set_class_wise_data(class_data)
                print("✅ Class-wise data synced")
                
                print("✅ Background sync completed")
            else:
                print("❌ Data entry not initialized")
            
            # Sleep for the configured interval
            interval = int(os.environ.get('SYNC_INTERVAL', 300))  # 5 minutes default
            time.sleep(interval)
            
        except Exception as e:
            print(f"❌ Background sync error: {e}")
            time.sleep(60)  # Wait 1 minute on error

if __name__ == "__main__":
    load_dotenv()
    os.environ['ENABLE_BACKGROUND_SYNC'] = 'true'  # Force enable for worker
    run_sync()
