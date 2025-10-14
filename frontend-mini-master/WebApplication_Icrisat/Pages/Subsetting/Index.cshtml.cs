using WebApplication_Icrisat.Models;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using OfficeOpenXml;
using System.IO;
using WebApplication_Icrisat.Services;

namespace WebApplication_Icrisat.Pages.Subsetting
{
    public class IndexModel : PageModel
    {
        private readonly ILogger<IndexModel> _logger;
        private readonly CsvDataService _csvService;
        private readonly string _dataFolder = "data";

        private static string NormalizeId(string? id)
        {
            return (id ?? string.Empty).Trim().ToUpperInvariant();
        }

        static IndexModel()
        {
            ExcelPackage.LicenseContext = LicenseContext.NonCommercial;
        }

        public IndexModel(/*IcristatDbContext context,*/ ILogger<IndexModel> logger)
        {
            //_context = context;
            _logger = logger;
            _csvService = new CsvDataService(Path.Combine(Directory.GetCurrentDirectory(), _dataFolder));
        }

        [BindProperty(SupportsGet = true)]
        public float TempMin { get; set; } = 0;
        [BindProperty(SupportsGet = true)]
        public float TempMax { get; set; } = 50;
        [BindProperty(SupportsGet = true)]
        public float HumidityMin { get; set; } = 0;
        [BindProperty(SupportsGet = true)]
        public float HumidityMax { get; set; } = 100;
        [BindProperty(SupportsGet = true)]
        public float RainfallMin { get; set; } = 0;
        [BindProperty(SupportsGet = true)]
        public float RainfallMax { get; set; } = 1300;

        [BindProperty(SupportsGet = true)]
        public string CropFilter { get; set; } = "All";

        [BindProperty(SupportsGet = true)]
        public string? LastQuery { get; set; }

        [BindProperty(SupportsGet = true)]
        public int PageIndex { get; set; } = 1;

        [BindProperty(SupportsGet = true)]
        public int PageSize { get; set; } = 250; // Number of records per page (increased default)

        public int TotalRecords { get; set; }
        public int TotalPages => (int)Math.Ceiling((double)TotalRecords / PageSize);

        public IList<CombinedResult> PassportResults { get; set; } = new List<CombinedResult>();

        public IActionResult OnPostAsync()
        {
            _logger.LogInformation($"Filtering with Temp: {TempMin}-{TempMax}, Humidity: {HumidityMin}-{HumidityMax}, Rainfall: {RainfallMin}-{RainfallMax}");
            try
            {
                float epsilon = 0.01f;
                // Read and merge all Characterization data
                var charFiles = new[] { "Characterization.csv", "Chickpea_Characterization.csv" };
                var allChars = charFiles.SelectMany(f => _csvService.ReadCharacterizationData(f)).ToList();
                
                // Read and merge all Passport data first
                var passFiles = new[] { "Passport (1).csv", "Chickpea_Pass.csv" };
                var allPass = passFiles.SelectMany(f => _csvService.ReadPassportData(f)).ToList();
                
                // Apply crop filter to passport data FIRST if specified
                var filteredPassport = allPass;
                if (!string.IsNullOrEmpty(CropFilter) && CropFilter != "All")
                {
                    filteredPassport = allPass.Where(p => p.Crop?.Equals(CropFilter, StringComparison.OrdinalIgnoreCase) == true).ToList();
                    _logger.LogInformation($"Applied crop filter: {CropFilter}, filtered passport records: {filteredPassport.Count}");
                }
                
                // Filter out records without latitude and longitude data
                filteredPassport = filteredPassport.Where(p => p.Latitude.HasValue && p.Longitude.HasValue).ToList();
                _logger.LogInformation($"After lat/long filter: {filteredPassport.Count} records with geographic data");
                
                // Get accession IDs from filtered passport data
                var passportAccessionIds = filteredPassport
                    .Where(p => !string.IsNullOrWhiteSpace(p.ICRISATAccessionIdentifier))
                    .Select(p => NormalizeId(p.ICRISATAccessionIdentifier))
                    .Distinct()
                    .ToHashSet();
                
                // Now filter characterization data to only include records that exist in filtered passport data
                var filteredChars = allChars
                    .Where(c =>
                        !string.IsNullOrWhiteSpace(c.ICRISATAccessionIdentifier) &&
                        passportAccessionIds.Contains(NormalizeId(c.ICRISATAccessionIdentifier)) &&
                        c.Temperature.HasValue && c.Humidity.HasValue && c.Rainfall.HasValue &&
                        (c.Temperature >= (TempMin - epsilon) && c.Temperature <= (TempMax + epsilon)) &&
                        (c.Humidity >= (HumidityMin - epsilon) && c.Humidity <= (HumidityMax + epsilon)) &&
                        (c.Rainfall >= (RainfallMin - epsilon) && c.Rainfall <= (RainfallMax + epsilon))
                    )
                    .ToList();
                var filteredAccessionIds = filteredChars
                    .Select(c => NormalizeId(c.ICRISATAccessionIdentifier))
                    .Where(id => !string.IsNullOrWhiteSpace(id))
                    .Distinct()
                    .ToList();
                TotalRecords = filteredAccessionIds.Count;
                if (TotalRecords > 0)
                {
                    var pagedAccessionIds = filteredAccessionIds
                        .Skip((PageIndex - 1) * PageSize)
                        .Take(PageSize)
                        .ToList();
                    var pagedIdSet = new HashSet<string>(pagedAccessionIds);
                    
                    // Filter passport data to only include the paged accession IDs
                    var pagedPassport = filteredPassport
                        .Where(p => !string.IsNullOrWhiteSpace(p.ICRISATAccessionIdentifier) && pagedIdSet.Contains(NormalizeId(p.ICRISATAccessionIdentifier)))
                        .ToList();

                    // Build dictionary safely: ignore null/empty keys and collapse duplicates by first
                    var charById = filteredChars
                        .Where(c => !string.IsNullOrWhiteSpace(c.ICRISATAccessionIdentifier))
                        .GroupBy(c => NormalizeId(c.ICRISATAccessionIdentifier))
                        .ToDictionary(
                            g => g.Key,
                            g => g
                                .OrderByDescending(x => (x.Temperature.HasValue ? 1 : 0) + (x.Humidity.HasValue ? 1 : 0) + (x.Rainfall.HasValue ? 1 : 0))
                                .First()
                        );

                    PassportResults = pagedPassport
                        .Select(p =>
                        {
                            var normId = NormalizeId(p.ICRISATAccessionIdentifier);
                            charById.TryGetValue(normId, out var ch);
                            return new CombinedResult
                            {
                                ICRISATAccessionIdentifier = p.ICRISATAccessionIdentifier!,
                                AccessionIdentifier = p.AccessionIdentifier,
                                Crop = p.Crop,
                                DOI = p.DOI,
                                Genus = p.Genus,
                                Species = p.Species,
                                Latitude = p.Latitude,
                                Longitude = p.Longitude,
                                Temperature = ch?.Temperature,
                                Humidity = ch?.Humidity,
                                Rainfall = ch?.Rainfall
                            };
                        })
                        .ToList();
                }
                else
                {
                    PassportResults = new List<CombinedResult>();
                }
            }
            catch (IOException ex)
            {
                _logger.LogError(ex, "File access error: {Message}", ex.Message);
                PassportResults = new List<CombinedResult>();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error filtering and retrieving passport data from CSV.");
                PassportResults = new List<CombinedResult>();
            }
            return Page();
        }

        public IActionResult OnGetAsync()
        {
            // Populate results using current querystring-bound filters so pagination preserves state
            return OnPostAsync();
        }

        public IActionResult OnPostExportToExcelAsync([FromBody] FilterModel filters)
        {
            try
            {
                float epsilon = 0.01f;
                // Read and merge all Characterization data
                var charFiles = new[] { "Characterization.csv", "Chickpea_Characterization.csv" };
                var allChars = charFiles.SelectMany(f => _csvService.ReadCharacterizationData(f)).ToList();
                
                // Read and merge all Passport data first
                var passFiles = new[] { "Passport (1).csv", "Chickpea_Pass.csv" };
                var allPass = passFiles.SelectMany(f => _csvService.ReadPassportData(f)).ToList();
                
                // Apply crop filter to passport data FIRST if specified
                var filteredPassport = allPass;
                if (!string.IsNullOrEmpty(filters.CropFilter) && filters.CropFilter != "All")
                {
                    filteredPassport = allPass.Where(p => p.Crop?.Equals(filters.CropFilter, StringComparison.OrdinalIgnoreCase) == true).ToList();
                }
                
                // Filter out records without latitude and longitude data
                filteredPassport = filteredPassport.Where(p => p.Latitude.HasValue && p.Longitude.HasValue).ToList();
                
                // Get accession IDs from filtered passport data
                var passportAccessionIds = filteredPassport
                    .Where(p => !string.IsNullOrWhiteSpace(p.ICRISATAccessionIdentifier))
                    .Select(p => NormalizeId(p.ICRISATAccessionIdentifier))
                    .Distinct()
                    .ToHashSet();
                
                // Now filter characterization data to only include records that exist in filtered passport data
                var filteredChars = allChars
                    .Where(c =>
                        !string.IsNullOrWhiteSpace(c.ICRISATAccessionIdentifier) &&
                        passportAccessionIds.Contains(NormalizeId(c.ICRISATAccessionIdentifier)) &&
                        c.Temperature.HasValue && c.Humidity.HasValue && c.Rainfall.HasValue &&
                        (c.Temperature >= (filters.TempMin - epsilon) && c.Temperature <= (filters.TempMax + epsilon)) &&
                        (c.Humidity >= (filters.HumidityMin - epsilon) && c.Humidity <= (filters.HumidityMax + epsilon)) &&
                        (c.Rainfall >= (filters.RainfallMin - epsilon) && c.Rainfall <= (filters.RainfallMax + epsilon))
                    )
                    .ToList();
                var filteredAccessionIds = filteredChars
                    .Select(c => NormalizeId(c.ICRISATAccessionIdentifier))
                    .Where(id => !string.IsNullOrWhiteSpace(id))
                    .Distinct()
                    .ToList();
                
                // Filter passport data to only include the filtered accession IDs
                var finalPassport = filteredPassport
                    .Where(p => !string.IsNullOrWhiteSpace(p.ICRISATAccessionIdentifier) && filteredAccessionIds.Contains(NormalizeId(p.ICRISATAccessionIdentifier)))
                    .ToList();

                var charById = filteredChars
                    .Where(c => !string.IsNullOrWhiteSpace(c.ICRISATAccessionIdentifier))
                    .GroupBy(c => NormalizeId(c.ICRISATAccessionIdentifier))
                    .ToDictionary(
                        g => g.Key,
                        g => g
                            .OrderByDescending(x => (x.Temperature.HasValue ? 1 : 0) + (x.Humidity.HasValue ? 1 : 0) + (x.Rainfall.HasValue ? 1 : 0))
                            .First()
                    );

                var combined = finalPassport.Select(p =>
                {
                    var normId = NormalizeId(p.ICRISATAccessionIdentifier);
                    charById.TryGetValue(normId, out var ch);
                    return new CombinedResult
                    {
                        ICRISATAccessionIdentifier = p.ICRISATAccessionIdentifier!,
                        AccessionIdentifier = p.AccessionIdentifier,
                        Crop = p.Crop,
                        DOI = p.DOI,
                        Genus = p.Genus,
                        Species = p.Species,
                        Latitude = p.Latitude,
                        Longitude = p.Longitude,
                        Temperature = ch?.Temperature,
                        Humidity = ch?.Humidity,
                        Rainfall = ch?.Rainfall
                    };
                }).ToList();
                using (var package = new OfficeOpenXml.ExcelPackage())
                {
                    var worksheet = package.Workbook.Worksheets.Add("Passport Data");
                    
                    // Check if any records have lat/long data
                    bool hasLatLongData = combined.Any(p => p.Latitude.HasValue || p.Longitude.HasValue);
                    
                    int colIndex = 1;
                    worksheet.Cells[1, colIndex++].Value = "ICRISAT Accession Identifier";
                    worksheet.Cells[1, colIndex++].Value = "Accession Identifier";
                    worksheet.Cells[1, colIndex++].Value = "Crop";
                    worksheet.Cells[1, colIndex++].Value = "DOI";
                    worksheet.Cells[1, colIndex++].Value = "Genus";
                    worksheet.Cells[1, colIndex++].Value = "Species";
                    
                    if (hasLatLongData)
                    {
                        worksheet.Cells[1, colIndex++].Value = "Latitude";
                        worksheet.Cells[1, colIndex++].Value = "Longitude";
                    }
                    
                    worksheet.Cells[1, colIndex++].Value = "Temperature";
                    worksheet.Cells[1, colIndex++].Value = "Humidity";
                    worksheet.Cells[1, colIndex++].Value = "Rainfall";
                    
                    int totalCols = colIndex - 1;
                    
                    using (var range = worksheet.Cells[1, 1, 1, totalCols])
                    {
                        range.Style.Font.Bold = true;
                        range.Style.Fill.PatternType = OfficeOpenXml.Style.ExcelFillStyle.Solid;
                        range.Style.Fill.BackgroundColor.SetColor(System.Drawing.Color.LightGray);
                    }
                    
                    int row = 2;
                    foreach (var item in combined)
                    {
                        colIndex = 1;
                        worksheet.Cells[row, colIndex++].Value = item.ICRISATAccessionIdentifier;
                        worksheet.Cells[row, colIndex++].Value = item.AccessionIdentifier;
                        worksheet.Cells[row, colIndex++].Value = item.Crop;
                        worksheet.Cells[row, colIndex++].Value = item.DOI;
                        worksheet.Cells[row, colIndex++].Value = item.Genus;
                        worksheet.Cells[row, colIndex++].Value = item.Species;
                        
                        if (hasLatLongData)
                        {
                            worksheet.Cells[row, colIndex++].Value = item.Latitude;
                            worksheet.Cells[row, colIndex++].Value = item.Longitude;
                        }
                        
                        worksheet.Cells[row, colIndex++].Value = item.Temperature;
                        worksheet.Cells[row, colIndex++].Value = item.Humidity;
                        worksheet.Cells[row, colIndex++].Value = item.Rainfall;
                        row++;
                    }
                    worksheet.Cells[worksheet.Dimension.Address].AutoFitColumns();
                    var content = package.GetAsByteArray();
                    var contentType = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
                    var fileName = $"ICRISAT_Data_Export_{DateTime.Now:yyyyMMdd_HHmmss}.xlsx";
                    Response.Headers.Append("Content-Disposition", $"attachment; filename={fileName}");
                    return File(content, contentType, fileName);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error exporting data to Excel from CSV");
                return BadRequest(new { error = "Failed to export data to Excel" });
            }
        }

        public class FilterModel
        {
            public float TempMin { get; set; }
            public float TempMax { get; set; }
            public float HumidityMin { get; set; }
            public float HumidityMax { get; set; }
            public float RainfallMin { get; set; }
            public float RainfallMax { get; set; }
            public string CropFilter { get; set; } = "All";
        }
    }
}