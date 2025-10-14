# CSV Bulk Upload Guide

## Overview
Upload multiple contacts at once using CSV files through the web dashboard.

## Access the Upload Page
1. Open web browser and navigate to: `http://localhost:8001`
2. Click on the **"Bulk Upload (CSV)"** tab
3. Select your CSV file and click "Upload Contacts"

## CSV Format Requirements

### Required Columns
- **name**: Contact's full name
- **phone**: Phone number with country code (e.g., +61421856756, +14693072939)

### Optional Columns
- **email**: Email address
- **contact_type**: Type of contact (friend, facility, general, etc.)
- **notes**: Additional notes about the contact

### Example CSV

```csv
name,phone,email,contact_type,notes
Daniel Clark,+61421856756,daniel@example.com,friend,Test contact - responds well to calls
Senthil Kumar,+61411314178,senthil@example.com,facility,Voicemail full
Hemant Sharma,+14693072939,hemant@example.com,friend,US based - good conversationalist
Kabeer Ahmed,+61455906866,kabeer@example.com,facility,Australia - needs delay warning
```

## How It Works

1. **Duplicate Detection**: The system automatically skips contacts with phone numbers that already exist in the database
2. **Validation**: Each row is validated to ensure required fields (name, phone) are present
3. **Error Reporting**: If any rows fail to import, you'll see detailed error messages
4. **Success Report**: After upload, you'll see:
   - Number of contacts successfully imported
   - Number of duplicates skipped
   - Any errors encountered

## Testing with Sample File

A sample CSV file is provided: `sample_contacts.csv`

To test:
1. Open the web dashboard at `http://localhost:8001`
2. Go to "Bulk Upload (CSV)" tab
3. Select `sample_contacts.csv` from your project directory
4. Click "Upload Contacts"
5. You should see: "Successfully uploaded 9 contacts!"

## Phone Number Format

**IMPORTANT**: Always include the country code in the phone number.

### Examples:
- ✅ **Correct**: +61421856756 (Australia)
- ✅ **Correct**: +14693072939 (USA)
- ✅ **Correct**: +442071234567 (UK)
- ❌ **Wrong**: 0421856756 (missing country code)
- ❌ **Wrong**: 4693072939 (missing + and country code)

### Country Code Reference:
- Australia: +61
- United States: +1
- United Kingdom: +44
- India: +91
- Canada: +1

## Creating Your CSV File

### Using Excel:
1. Create spreadsheet with columns: name, phone, email, contact_type, notes
2. Fill in contact data
3. Save as: "File > Save As > CSV (Comma delimited)"

### Using Google Sheets:
1. Create spreadsheet with columns: name, phone, email, contact_type, notes
2. Fill in contact data
3. Download as: "File > Download > Comma Separated Values (.csv)"

### Using a Text Editor:
1. Create a new file with .csv extension
2. First line should be: `name,phone,email,contact_type,notes`
3. Each subsequent line is one contact with values separated by commas
4. Save the file

## Tips

1. **Start Small**: Test with 2-3 contacts first to ensure your format is correct
2. **No Special Characters**: Avoid special characters in names and notes (except in phone numbers)
3. **Consistent Format**: Keep phone number format consistent throughout the file
4. **Backup First**: If updating existing contacts, export current data first
5. **Check Duplicates**: The system will skip duplicates, so you can safely re-upload

## Troubleshooting

### "Missing name or phone" Error
- Check that every row has both name and phone values
- Make sure there are no empty rows in your CSV

### "File must be a CSV file" Error
- Ensure your file has .csv extension
- If using Excel, make sure you saved as CSV format, not .xlsx

### Contacts Not Showing Up
- Refresh the page
- Check the success message for the number of contacts imported
- Duplicate phone numbers are automatically skipped

## Making Calls to Uploaded Contacts

After uploading contacts, you can call them using:

### Method 1: Python Script
```python
import requests

API_URL = "http://localhost:8001/api/calls/facility-test"

# Get contact from database by name
response = requests.post(API_URL, data={
    "name": "Daniel Clark",
    "phone": "+61421856756",
    "caller_name": "Krishnaji's CTO office",
    "custom_subject": "follow-up conversation"
})

print(response.json())
```

### Method 2: Web Dashboard
1. Go to "Facility Test Call" or "Personal Message Call" tab
2. Enter the contact's name and phone number
3. Click "Make Call" or "Make Test Call"

### Method 3: Bulk Calling Script
(You can create a script to loop through contacts and make calls)

```python
import requests
import csv
import time

API_URL = "http://localhost:8001/api/calls/facility-test"

# Read contacts from CSV
with open('sample_contacts.csv', 'r') as f:
    reader = csv.DictReader(f)
    for contact in reader:
        # Make call
        response = requests.post(API_URL, data={
            "name": contact['name'],
            "phone": contact['phone']
        })
        print(f"Called {contact['name']}: {response.json()}")

        # Wait 60 seconds between calls
        time.sleep(60)
```

## Support

For issues or questions:
- Check the application logs: `docker-compose logs -f app`
- Review this guide
- Check the sample CSV file for format reference
