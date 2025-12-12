# Yoli Monthly Call Summary with Pagination - Make.com Blueprint

## Overview

This Make.com blueprint automatically retrieves all calls from Retell AI for the previous month and calculates:
- **Total number of calls**
- **Total minutes** (sum of all call durations)

The scenario uses pagination to handle any number of calls, automatically looping through batches of up to 1000 calls until all calls in the date range are retrieved.

## Features

- **Automatic Date Range**: Calculates the previous month's date range (first day of last month to first day of current month)
- **Pagination Loop**: Automatically fetches all calls using pagination, handling datasets larger than 1000 calls
- **Real-time Counters**: Tracks total calls and total minutes as it processes each call
- **Batch Tracking**: Counts the number of API requests made
- **Final Summary**: Outputs final totals with minutes rounded to 2 decimal places

## How It Works

### Module Flow

1. **Initialize Date Variables** (Modules 1-2)
   - Sets `Start` date to first day of previous month (Unix timestamp)
   - Sets `End` date to first day of current month (Unix timestamp)

2. **Initialize Counters** (Modules 3-6)
   - `TotalCalls`: Starts at 0, increments for each call
   - `TotalMinutes`: Starts at 0, accumulates call durations
   - `PaginationKey`: Starts empty, stores the last call_id from each batch
   - `BatchCount`: Tracks how many API requests have been made

3. **Fetch Calls Loop** (Module 7)
   - Makes HTTP POST request to Retell AI `/v2/list-calls` endpoint
   - Includes filter criteria: ended, inbound, phone_call, successful
   - Uses date range from Start to End
   - Limits to 1000 calls per request (maximum allowed)
   - Includes `pagination_key` if not empty (for subsequent requests)

4. **Increment Batch Counter** (Module 8)
   - Adds 1 to `BatchCount` after each API request

5. **Process Each Call** (Modules 9-11)
   - **Iterator** (Module 9): Loops through each call in the response array
   - **Increment Total Calls** (Module 10): Adds 1 to `TotalCalls` for each call
   - **Add Duration** (Module 11): Converts `duration_ms` to minutes (÷ 60000) and adds to `TotalMinutes`

6. **Prepare for Next Page** (Modules 12-13)
   - **Array Aggregator** (Module 12): Collects all `call_id` values from the current batch
   - **Update Pagination Key** (Module 13): Sets `PaginationKey` to the last `call_id` from the batch

7. **Loop Control** (Module 14)
   - **Repeater**: Loops back to Module 7 if exactly 1000 calls were returned
   - **Filter Condition**: `length(7.data) = 1000`
   - **Max Iterations**: 100 (safety limit to prevent infinite loops)
   - If fewer than 1000 calls are returned, the loop exits

8. **Final Output** (Modules 15-16)
   - **FinalTotalCalls** (Module 15): Stores the final count of total calls
   - **FinalTotalMinutes** (Module 16): Stores the final total minutes, rounded to 2 decimal places

## Installation Instructions

1. **Download the Blueprint**
   - Save `YoliMonthlyCallSummary_Final.blueprint.json` to your computer

2. **Import into Make.com**
   - Log in to your Make.com account
   - Go to Scenarios
   - Click "Create a new scenario"
   - Click the three-dot menu (⋯) in the bottom toolbar
   - Select "Import Blueprint"
   - Upload the `YoliMonthlyCallSummary_Final.blueprint.json` file

3. **Configure API Credentials**
   - The blueprint references API Key ID `78759` for Retell AI authentication
   - You'll need to update this to your own Retell AI API key:
     - Click on Module 7 (HTTP Request)
     - In the "Credentials" field, select or create a new API Key connection
     - Connection type: **API Key**
     - Add your Retell AI API key in Bearer token format
     - Header name: `Authorization`
     - Header value: `Bearer YOUR_RETELL_API_KEY`

4. **Test the Scenario**
   - Click "Run once" to test the scenario
   - Monitor the execution to ensure it's working correctly
   - Check the final variables `FinalTotalCalls` and `FinalTotalMinutes`

5. **Schedule (Optional)**
   - If you want this to run automatically each month:
     - Add a "Schedule" trigger module at the beginning
     - Set it to run on the 1st day of each month
     - Connect it to the existing flow

## Output Variables

After the scenario completes, you can access these variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `FinalTotalCalls` | Total number of calls retrieved | `2` |
| `FinalTotalMinutes` | Total duration in minutes (rounded to 2 decimals) | `4.51` |
| `BatchCount` | Number of API requests made | `1` |
| `Start` | Start timestamp (Unix milliseconds) | `1733011200000` |
| `End` | End timestamp (Unix milliseconds) | `1735689600000` |

## Pagination Logic Explained

The Retell AI API uses **cursor-based pagination** with the following behavior:

- **First Request**: No `pagination_key` is sent (or sent as empty string)
- **Subsequent Requests**: The `pagination_key` is set to the last `call_id` from the previous response
- **Loop Condition**: Continue looping if exactly 1000 calls are returned (indicates more pages exist)
- **Exit Condition**: If fewer than 1000 calls are returned, all calls have been retrieved

### Example Flow

**Scenario A: 2 calls total**
1. Request 1: Returns 2 calls → Loop exits (< 1000)
2. Final: `TotalCalls = 2`

**Scenario B: 2,500 calls total**
1. Request 1: Returns 1000 calls, last call_id = `call_abc123`
2. Request 2: Uses `pagination_key = call_abc123`, returns 1000 calls, last call_id = `call_def456`
3. Request 3: Uses `pagination_key = call_def456`, returns 500 calls → Loop exits (< 1000)
4. Final: `TotalCalls = 2500`

## Troubleshooting

### Issue: Empty `pagination_key` causes error

**Solution**: The blueprint uses `jsonObject` input method which handles empty strings properly. Make.com will omit the `pagination_key` field if it's empty, which is the correct behavior for the first request.

### Issue: Loop doesn't exit

**Solution**: Check the filter condition on Module 14 (Repeater). It should be:
- Condition: `length(7.data)` equals `1000`
- This ensures the loop only continues when a full batch of 1000 calls is returned

### Issue: Incorrect total minutes

**Solution**: Verify that Module 11 uses the correct formula:
- `{{add(4.TotalMinutes; divide(9.duration_ms; 60000))}}`
- This converts milliseconds to minutes by dividing by 60,000

### Issue: API authentication fails

**Solution**: 
- Verify your Retell AI API key is correct
- Ensure the API key has permissions to list calls
- Check that the Bearer token format is correct: `Bearer YOUR_API_KEY`

## Customization Options

### Change Date Range

To query a different time period, modify Modules 1 and 2:

**Last 7 days:**
```
Start: {{formatDate(parseDate(formatDate(addDays(now; -7); "YYYY-MM-DDT00:00:00Z")); "x")}}
End: {{formatDate(parseDate(now); "x")}}
```

**Current month:**
```
Start: {{formatDate(parseDate(formatDate(now; "YYYY-MM-01T00:00:00Z")); "x")}}
End: {{formatDate(parseDate(now); "x")}}
```

### Change Filter Criteria

To modify which calls are included, edit the `filter_criteria` in Module 7:

**Include outbound calls:**
```json
"direction": ["inbound", "outbound"]
```

**Include unsuccessful calls:**
```json
"call_successful": [true, false]
```

**Specific agent only:**
```json
"agent_id": ["agent_YOUR_AGENT_ID_HERE"]
```

### Add More Metrics

To track additional metrics, add new variables and calculations:

**Average call duration:**
- Add a final module: `{{divide(4.TotalMinutes; 3.TotalCalls)}}`

**Total cost:**
- In Module 11, add: `{{add(TotalCost; 9.call_cost.combined_cost)}}`

## API Reference

This blueprint uses the Retell AI List Calls API:

- **Endpoint**: `POST https://api.retellai.com/v2/list-calls`
- **Documentation**: https://docs.retellai.com/api-references/list-calls
- **Authentication**: Bearer token in Authorization header
- **Rate Limits**: Check Retell AI documentation for current limits

## Support

For issues with:
- **This blueprint**: Check the troubleshooting section above
- **Make.com platform**: Visit https://www.make.com/en/help
- **Retell AI API**: Visit https://docs.retellai.com or contact Retell AI support

## Version History

- **v1.0** (2024-12-11): Initial release with pagination support
  - Automatic date range calculation
  - Pagination loop for unlimited calls
  - Total calls and minutes tracking
  - Batch counter for monitoring

## License

This blueprint is provided as-is for use with Make.com and Retell AI services.
