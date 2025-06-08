using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Newtonsoft.Json;
using System.Collections.Generic;
using System.Linq;
using Microsoft.AspNetCore.Http;
using Newtonsoft.Json.Linq;
using System;

public class AccessionData
{
    [JsonExtensionData]
    public Dictionary<string, object> AdditionalProperties { get; set; } = new Dictionary<string, object>();
}

public class SearchResponse
{
    [JsonProperty("results")]
    public List<AccessionData> Results { get; set; } = new();

    [JsonProperty("data")]
    public List<AccessionData> Data
    {
        get => Results ?? new List<AccessionData>();
        set => Results = value;
    }

    [JsonProperty("accession_ids")]
    private List<string> AccessionIds
    {
        set
        {
            if (value != null)
            {
                Results = value.Select(id => new AccessionData()).ToList();
            }
        }
    }
}

public class IndexModel : PageModel
{
    private readonly HttpClient _httpClient;

    public IndexModel()
    {
        _httpClient = new HttpClient();
    }

    [BindProperty]
    public string? UserInput { get; set; }

    public List<AccessionData>? AllData { get; set; }
    public string? ResponseMessage { get; set; }
    public string? LastSearchQuery { get; set; }
    public string? TableDataJson { get; set; }
    public string? DebugInfo { get; set; }

    public async Task<IActionResult> OnPostAsync()
    {
        if (string.IsNullOrWhiteSpace(UserInput))
        {
            ResponseMessage = "Please enter a query.";
            return Page();
        }

        var requestBody = new { query = UserInput };
        var json = JsonConvert.SerializeObject(requestBody);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        string flaskApiUrl = "http://127.0.0.1:5000/search";

        try
        {
            // Add headers that might help with CORS
            _httpClient.DefaultRequestHeaders.Clear();
            _httpClient.DefaultRequestHeaders.Add("Accept", "application/json");
            _httpClient.DefaultRequestHeaders.Add("User-Agent", "ASP.NET-Core-App");

            HttpResponseMessage response = await _httpClient.PostAsync(flaskApiUrl, content);
            if (response.IsSuccessStatusCode)
            {
                var jsonString = await response.Content.ReadAsStringAsync();

                HttpContext.Session.SetString("RawResponse", jsonString);
                HttpContext.Session.SetString("AllData", jsonString);
                HttpContext.Session.SetString("LastSearchQuery", UserInput);

                return RedirectToPage();
            }
            else
            {
                var errorContent = await response.Content.ReadAsStringAsync();
                ResponseMessage = $"Error from Flask server: {response.StatusCode} - {errorContent}";
            }
        }
        catch (HttpRequestException ex)
        {
            ResponseMessage = $"Could not connect to Flask server. Make sure it is running. Error: {ex.Message}";
        }

        return Page();
    }

    public void OnGet()
    {
        LastSearchQuery = HttpContext.Session.GetString("LastSearchQuery");
        var json = HttpContext.Session.GetString("AllData");

        if (string.IsNullOrEmpty(json))
        {
            ResponseMessage = "No data found in session. Please perform a search.";
            return;
        }

        DebugInfo = $"Raw JSON length: {json.Length} characters";

        try
        {
            JToken parsedToken = JToken.Parse(json);
            AllData = new List<AccessionData>();

            DebugInfo += $"\nJSON Type: {parsedToken.Type}";

            if (parsedToken.Type == JTokenType.Array)
            {
                DebugInfo += "\nProcessing as Array";
                foreach (JObject item in parsedToken as JArray)
                {
                    AllData.Add(ConvertToAccessionData(item));
                }
            }
            else if (parsedToken.Type == JTokenType.Object)
            {
                JObject jsonObj = (JObject)parsedToken;
                DebugInfo += $"\nObject keys: {string.Join(", ", jsonObj.Properties().Select(p => p.Name))}";

                if (jsonObj["results"] is JArray resultsArray)
                {
                    DebugInfo += $"\nFound 'results' array with {resultsArray.Count} items";
                    foreach (JObject item in resultsArray)
                    {
                        AllData.Add(ConvertToAccessionData(item));
                    }
                }
                else if (jsonObj["data"] is JArray dataArray)
                {
                    DebugInfo += $"\nFound 'data' array with {dataArray.Count} items";
                    foreach (JObject item in dataArray)
                    {
                        AllData.Add(ConvertToAccessionData(item));
                    }
                }
                else
                {
                    DebugInfo += "\nProcessing entire object as single item";
                    AllData.Add(ConvertToAccessionData(jsonObj));
                }
            }

            DebugInfo += $"\nParsed {AllData?.Count ?? 0} items";

            if (AllData == null || AllData.Count == 0)
            {
                ResponseMessage = "No accession data could be extracted from the response.";
                return;
            }
        }
        catch (Exception ex)
        {
            ResponseMessage = $"Error processing JSON: {ex.Message}";
            DebugInfo += $"\nException: {ex.Message}";
            return;
        }

        if (AllData == null || AllData.Count == 0)
        {
            ResponseMessage = "No search results to display.";
            return;
        }

        // Prepare data for jQuery DataTable
        var allProperties = new HashSet<string>();
        foreach (var item in AllData)
        {
            foreach (var prop in item.AdditionalProperties.Keys)
            {
                allProperties.Add(prop);
            }
        }

        var sortedProps = allProperties.OrderBy(p => p).ToList();
        DebugInfo += $"\nFound properties: {string.Join(", ", sortedProps)}";

        var tableData = new List<Dictionary<string, object>>();

        foreach (var item in AllData)
        {
            var row = new Dictionary<string, object>();
            foreach (var prop in sortedProps)
            {
                object cellValue = item.AdditionalProperties.ContainsKey(prop)
                    ? item.AdditionalProperties[prop] ?? ""
                    : "";
                row[prop] = cellValue;
            }
            tableData.Add(row);
        }

        TableDataJson = JsonConvert.SerializeObject(new { 
            columns = sortedProps, 
            data = tableData 
        }, new JsonSerializerSettings 
        { 
            NullValueHandling = NullValueHandling.Include,
            DefaultValueHandling = DefaultValueHandling.Include
        });

        ResponseMessage = "Data loaded successfully.";
    }

    private AccessionData ConvertToAccessionData(JObject item)
    {
        var accession = new AccessionData();

        foreach (var prop in item.Properties())
        {
            // Handle different JSON value types properly
            object value = prop.Value.Type switch
            {
                JTokenType.Null => "",
                JTokenType.String => prop.Value.Value<string>() ?? "",
                JTokenType.Integer => prop.Value.Value<long>(),
                JTokenType.Float => prop.Value.Value<double>(),
                JTokenType.Boolean => prop.Value.Value<bool>(),
                JTokenType.Date => prop.Value.Value<DateTime>(),
                _ => prop.Value.ToString()
            };
            
            accession.AdditionalProperties[prop.Name] = value;
        }

        return accession;
    }
}