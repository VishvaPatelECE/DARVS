import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1D1Bb2aiBGanKHCBS8lbFZzro1_uPmc41nFAPgBChLS0"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]

creds = Credentials.from_service_account_file(
    "gcp_credentials.json",
    scopes=SCOPES
)

client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SHEET_ID)

# Main log sheet
main_sheet = spreadsheet.sheet1

# Statistics tab (must exist)
stats_sheet = spreadsheet.worksheet("Statistics")


# -------------------------------
# Append Log + Color + Stats
# -------------------------------

def append_to_sheet(row):

    main_sheet.append_row(row)

    last_row = len(main_sheet.get_all_values())

    status = row[3]

    if status == "SUCCESS":
        color = {"red": 0.8, "green": 1.0, "blue": 0.8}
    elif status == "FAILED":
        color = {"red": 1.0, "green": 0.8, "blue": 0.8}
    elif status == "LIVENESS_FAILED":
        color = {"red": 1.0, "green": 0.9, "blue": 0.6}
    else:
        color = None

    if color:
        main_sheet.format(
            f"A{last_row}:F{last_row}",
            {"backgroundColor": color}
        )

    update_statistics(row)


# -------------------------------
# Statistics Logic
# -------------------------------
def update_statistics(row):

    try:
        status = row[3]
        liveness = row[4]

        stats = stats_sheet.get_all_values()

        required_structure = [
            ["Metric", "Count"],
            ["Total Attempts", "0"],
            ["Success", "0"],
            ["Failed", "0"],
            ["Liveness Failed", "0"]
        ]

        # If structure missing or corrupted → reset
        if len(stats) < 5 or stats[0][0] != "Metric":
            stats_sheet.clear()
            for r in required_structure:
                stats_sheet.append_row(r)
            stats = stats_sheet.get_all_values()

        # Re-fetch after possible rebuild
        stats = stats_sheet.get_all_values()

        metrics = {}
        for i in range(1, len(stats)):
            metrics[stats[i][0]] = i + 1

        def increment(metric_name):
            row_index = metrics[metric_name]
            current = int(stats[row_index - 1][1])
            stats_sheet.update_cell(row_index, 2, current + 1)

        increment("Total Attempts")

        if status == "SUCCESS":
            increment("Success")

        if status == "FAILED":
            increment("Failed")

        if liveness == "LIVENESS_FAILED":
            increment("Liveness Failed")

    except Exception as e:
        print("Statistics update error:", e)