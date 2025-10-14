using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using CsvHelper.Configuration.Attributes;

namespace WebApplication_Icrisat.Models
{
    [Table("charecterstics")]
    public class Characterization
    {
        [Key] 
        [Name("ICRISAT accession identifier")]
        public string ICRISATAccessionIdentifier { get; set; } = string.Empty;

        [Name("Race")]
        public string? Race { get; set; }

        [Name("Temperature")]
        public float? Temperature { get; set; }

        [Name("Humidity")]
        public float? Humidity { get; set; }

        [Name("Rainfall")]
        public float? Rainfall { get; set; }

        [Name("Plant height (cm)-postrainy")]
        public float? PlantHeightCmPostrainy { get; set; }

        [Name("Plant height (cm)-rainy")]
        public float? PlantHeightCmRainy { get; set; }

        [Name("Plant pigmentation")]
        public string? PlantPigmentation { get; set; }

        [Name("Basal tillers number")]
        public int? BasalTillersNumber { get; set; }

        [Name("Nodal tillering")]
        public string? NodalTillering { get; set; }

        [Name("Midrib color")]
        public string? MidribColor { get; set; }

        [Name("Days to flowering-postrainy")]
        public int? DaysToFloweringPostrainy { get; set; }

        [Name("Days to flowering-rainy")]
        public int? DaysToFloweringRainy { get; set; }

        [Name("Panicle exertion (cm)")]
        public float? PanicleExertionCm { get; set; }

        [Name("Panicle length (cm)")]
        public float? PanicleLengthCm { get; set; }

        [Name("Panicle width (cm)")]
        public float? PanicleWidthCm { get; set; }

        [Name("Panicle compactness and shape")]
        public string? PanicleCompactnessAndShape { get; set; }

        [Name("Glume color")]
        public string? GlumeColor { get; set; }

        [Name("Glume covering")]
        public string? GlumeCovering { get; set; }

        [Name("Seed color")]
        public string? SeedColor { get; set; }

        [Name("Seed lustre")]
        public string? SeedLustre { get; set; }

        [Name("Seed subcoat")]
        public string? SeedSubcoat { get; set; }

        [Name("Seed size (mm)")]
        public float? SeedSizeMm { get; set; }

        [Name("100 Seed weight (g)")]
        public float? SeedWeight100G { get; set; }

        [Name("Endosperm texture")]
        public string? EndospermTexture { get; set; }

        [Name("Thresability")]
        public string? Thresability { get; set; }

        [Name("Shoot fly-rainy")]
        public string? ShootFlyRainy { get; set; }

        [Name("Shoot fly-postrainy")]
        public string? ShootFlyPostrainy { get; set; }

        [Name("Downy mildew % (field)")]
        public string? DownyMildewField { get; set; }

        [Name("Downy mildew % (glasshouse)")]
        public string? DownyMildewGlasshouse { get; set; }

        [Name("Stem borer")]
        public string? StemBorer { get; set; }

        [Name("Anthracnose")]
        public string? Anthracnose { get; set; }

        [Name("Grain mold")]
        public string? GrainMold { get; set; }

        [Name("Leaf blight")]
        public string? LeafBlight { get; set; }

        [Name("Midge")]
        public string? Midge { get; set; }

        [Name("Headbug")]
        public string? Headbug { get; set; }

        [Name("Rust")]
        public string? Rust { get; set; }

        [Name("Strigol control")]
        public string? StrigolControl { get; set; }

        [Name("Protein (%)")]
        public float? Protein { get; set; }

        [Name("Lysine (%)")]
        public float? Lysine { get; set; }

        [Name("Remarks")]
        public string? Remarks { get; set; }

        [Name("Year of characterization")]
        public int? YearOfCharacterization { get; set; }
    }
}
