using CsvHelper;
using CsvHelper.Configuration;
using CsvHelper.TypeConversion;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using WebApplication_Icrisat.Models; 

namespace WebApplication_Icrisat.Services 
{
    public class YearConverter : DefaultTypeConverter
    {
        public override object? ConvertFromString(string? text, IReaderRow row, MemberMapData memberMapData)
        {
            if (string.IsNullOrWhiteSpace(text) || text == "NULL") return null;

            // Try to extract a 4-digit year from the text
            var match = Regex.Match(text, @"\b\d{4}\b");
            if (match.Success)
            {
                if (int.TryParse(match.Value, out int year))
                {
                    return year;
                }
            }

            return null;
        }
    }

    public class CharacterizationMap : ClassMap<Characterization>
    {
        public CharacterizationMap()
        {
            Map(m => m.ICRISATAccessionIdentifier).Name("ICRISAT accession identifier");
            Map(m => m.Race).Name("Race").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.Temperature).Name("Temperature").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.Humidity).Name("Humidity").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.Rainfall).Name("Rainfall").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.PlantHeightCmPostrainy).Name("Plant height (cm)-postrainy").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.PlantHeightCmRainy).Name("Plant height (cm)-rainy").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.PlantPigmentation).Name("Plant pigmentation").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.BasalTillersNumber).Name("Basal tillers number").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.NodalTillering).Name("Nodal tillering").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.MidribColor).Name("Midrib color").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.DaysToFloweringPostrainy).Name("Days to flowering-postrainy").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.DaysToFloweringRainy).Name("Days to flowering-rainy").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.PanicleExertionCm).Name("Panicle exertion (cm)").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.PanicleLengthCm).Name("Panicle length (cm)").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.PanicleWidthCm).Name("Panicle width (cm)").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.PanicleCompactnessAndShape).Name("Panicle compactness and shape").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.GlumeColor).Name("Glume color").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.GlumeCovering).Name("Glume covering").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.SeedColor).Name("Seed color").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.SeedLustre).Name("Seed lustre").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.SeedSubcoat).Name("Seed subcoat").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.SeedSizeMm).Name("Seed size (mm)").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.SeedWeight100G).Name("100 Seed weight (g)").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.EndospermTexture).Name("Endosperm texture").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.Thresability).Name("Thresability").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.ShootFlyRainy).Name("Shoot fly-rainy").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.ShootFlyPostrainy).Name("Shoot fly-postrainy").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.DownyMildewField).Name("Downy mildew % (field)").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.DownyMildewGlasshouse).Name("Downy mildew % (glasshouse)").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.StemBorer).Name("Stem borer").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.Anthracnose).Name("Anthracnose").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.GrainMold).Name("Grain mold").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.LeafBlight).Name("Leaf blight").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.Midge).Name("Midge").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.Headbug).Name("Headbug").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.Rust).Name("Rust").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.StrigolControl).Name("Strigol control").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.Protein).Name("Protein (%)").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.Lysine).Name("Lysine (%)").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.Remarks).Name("Remarks").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.YearOfCharacterization).Name("Year of characterization").TypeConverter<YearConverter>();
        }
    }

    public class PassportDataMap : ClassMap<PassportData>
    {
        public PassportDataMap()
        {
            Map(m => m.ICRISATAccessionIdentifier).Name("ICRISAT accession identifier");
            Map(m => m.AccessionIdentifier).Name("Accession identifier").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.Crop).Name("Crop").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.DOI).Name("DOI").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.LocalName).Name("Local name").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.Genus).Name("Genus").TypeConverterOption.NullValues("NULL", "");
            Map(m => m.Species).Name("Species").TypeConverterOption.NullValues("NULL", "");

            // Latitude/Longitude flexible handling
            Map(m => m.Latitude)
                .Convert(args =>
                {
                    var r = args.Row;
                    var candidates = new[]
                    {
                        "Latitude","LATITUDE","latitude","Lat","LAT",
                        "Latitude (decimal degrees)","Latitude (DD)","Decimal Latitude",
                        "Lat_dec","LatDD","Lat (deg)","Lat_deg","Latitude DD","Lat DD"
                    };
                    foreach (var c in candidates)
                    {
                        if (r.TryGetField(c, out string? raw) && !string.IsNullOrWhiteSpace(raw) && raw != "NULL")
                        {
                            if (double.TryParse(raw, NumberStyles.Any, CultureInfo.InvariantCulture, out var val))
                                return val;
                            if (double.TryParse(raw, NumberStyles.Any, CultureInfo.CurrentCulture, out val))
                                return val;
                        }
                    }
                    return (double?)null;
                });

            Map(m => m.Longitude)
                .Convert(args =>
                {
                    var r = args.Row;
                    var candidates = new[]
                    {
                        "Longitude","LONGITUDE","longitude","Long","LON",
                        "Longitude (decimal degrees)","Longitude (DD)","Decimal Longitude",
                        "Lon_dec","LonDD","Long (deg)","Lon_deg","Longitude DD","Lon DD"
                    };
                    foreach (var c in candidates)
                    {
                        if (r.TryGetField(c, out string? raw) && !string.IsNullOrWhiteSpace(raw) && raw != "NULL")
                        {
                            if (double.TryParse(raw, NumberStyles.Any, CultureInfo.InvariantCulture, out var val))
                                return val;
                            if (double.TryParse(raw, NumberStyles.Any, CultureInfo.CurrentCulture, out val))
                                return val;
                        }
                    }
                    return (double?)null;
                });
        }
    }

    public class CsvDataService
    {
        private readonly string _dataFolder;
        public CsvDataService(string dataFolder)
        {
            _dataFolder = dataFolder;
        }

        public List<PassportData> ReadPassportData(string fileName)
        {
            var filePath = Path.Combine(_dataFolder, fileName);
            var config = new CsvConfiguration(CultureInfo.InvariantCulture)
            {
                MissingFieldFound = null,
                HeaderValidated = null,
                BadDataFound = null
            };

            try
            {
                using (var reader = new StreamReader(filePath))
                using (var csv = new CsvReader(reader, config))
                {
                    csv.Context.RegisterClassMap<PassportDataMap>();
                    return csv.GetRecords<PassportData>().ToList();
                }
            }
            catch (IOException ex)
            {
                throw new IOException($"Cannot access file '{fileName}'. Please ensure the file is not open in another application and try again.", ex);
            }
        }

        public List<Characterization> ReadCharacterizationData(string fileName)
        {
            var filePath = Path.Combine(_dataFolder, fileName);
            var config = new CsvConfiguration(CultureInfo.InvariantCulture)
            {
                MissingFieldFound = null,
                HeaderValidated = null,
                BadDataFound = null
            };

            try
            {
                using (var reader = new StreamReader(filePath))
                using (var csv = new CsvReader(reader, config))
                {
                    csv.Context.RegisterClassMap<CharacterizationMap>();
                    return csv.GetRecords<Characterization>().ToList();
                }
            }
            catch (IOException ex)
            {
                throw new IOException($"Cannot access file '{fileName}'. Please ensure the file is not open in another application and try again.", ex);
            }
        }
    }
}
