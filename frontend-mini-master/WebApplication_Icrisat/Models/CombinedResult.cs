using System.ComponentModel.DataAnnotations.Schema;

namespace WebApplication_Icrisat.Models
{
    public class CombinedResult
    {
        public string ICRISATAccessionIdentifier { get; set; } = string.Empty;
        public string? AccessionIdentifier { get; set; }
        public string? Crop { get; set; }
        public string? DOI { get; set; }
        public string? Genus { get; set; }
        public string? Species { get; set; }
        public double? Latitude { get; set; }
        public double? Longitude { get; set; }

        public float? Temperature { get; set; }
        public float? Humidity { get; set; }
        public float? Rainfall { get; set; }
    }
}